import json
from datetime import datetime, timedelta
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Sum, Count
from django.http import JsonResponse, HttpResponseForbidden, FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_POST
from .models import (Doctor, Patient, Appointment, DoctorSchedule, UserProfile,
                     MedicalRecord, LabResult, Prescription, Payment, ReminderLog, Service)
from .forms import PatientRegistrationForm, MedicalRecordForm, LabResultForm, PrescriptionForm
from .forms import PatientRegistrationForm, MedicalRecordForm, LabResultForm, PrescriptionForm
from django import forms
from .models import DoctorSchedule
def _profile(user):
    return getattr(user, "clinic_profile", None)

def _patient_for(user):
    return getattr(user, "patient_profile", None)

def _doctor_for(user):
    return getattr(user, "doctor_profile", None)

def _is_staff_role(user):
    profile = _profile(user)
    return user.is_superuser or user.is_staff or (profile and profile.role in {"reception", "accountant", "lab", "manager"})

def _doctor_or_staff(user):
    return _is_staff_role(user) or _doctor_for(user) is not None

def doctor_or_staff_required(view):
    return login_required(user_passes_test(_doctor_or_staff, login_url="home")(view))

def staff_required(view):
    return login_required(user_passes_test(_is_staff_role, login_url="home")(view))


def register_patient(request):
    if request.user.is_authenticated:
        return redirect("portal")
    form = PatientRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.email = form.cleaned_data["email"]
        user.save()
        Patient.objects.create(user=user, full_name=form.cleaned_data["full_name"], phone=form.cleaned_data["phone"], email=user.email)
        UserProfile.objects.create(user=user, role="patient", phone=form.cleaned_data["phone"])
        login(request, user)
        messages.success(request, "Shaxsiy kabinetingiz yaratildi.")
        return redirect("portal")
    return render(request, "registration/register.html", {"form": form})

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff, login_url="home")
def admin_panel(request):
    """Sayt ichidagi alohida administrator boshqaruv paneli."""
    today = timezone.localdate()
    context = {
        "doctor_count": Doctor.objects.filter(is_active=True).count(),
        "patient_count": Patient.objects.count(),
        "today_count": Appointment.objects.filter(appointment_time__date=today).exclude(status="cancelled").count(),
        "pending_count": Appointment.objects.filter(status="pending").count(),
        "service_count": Service.objects.filter(is_active=True).count(),
        "recent_appointments": Appointment.objects.select_related("patient", "doctor").order_by("-appointment_time")[:10],
    }
    return render(request, "portal/admin_panel.html", context)


@login_required
def doctor_panel(request):
    """Shifokor uchun sayt ichidagi alohida boshqaruv paneli."""
    doctor = _doctor_for(request.user)
    if not doctor:
        return redirect("portal")
    appointments = doctor.appointments.select_related("patient", "service").order_by("appointment_time")
    return render(request, "portal/doctor.html", {
        "doctor": doctor,
        "appointments": appointments[:50],
        "records": doctor.medical_records.select_related("patient")[:10],
        "prescriptions": doctor.prescriptions.select_related("patient")[:10],
    })


@login_required
def patient_panel(request):
    """Bemor uchun sayt ichidagi alohida shaxsiy boshqaruv paneli."""
    patient = _patient_for(request.user)
    if not patient:
        return redirect("portal")
    appointments = patient.appointments.select_related("doctor", "service").order_by("-appointment_time")
    return render(request, "portal/patient.html", {
        "patient": patient,
        "appointments": appointments[:20],
        "records": patient.medical_records.all()[:10],
        "labs": patient.lab_results.all()[:10],
        "prescriptions": patient.prescriptions.all()[:10],
        "payments": Payment.objects.filter(appointment__patient=patient).order_by("-created_at")[:10],
    })


@login_required
def portal(request):
    patient = _patient_for(request.user)
    doctor = _doctor_for(request.user)
    if patient:
        appointments = patient.appointments.select_related("doctor", "service").order_by("-appointment_time")
        return render(request, "portal/patient.html", {"patient": patient, "appointments": appointments[:20], "records": patient.medical_records.all()[:10], "labs": patient.lab_results.all()[:10], "prescriptions": patient.prescriptions.all()[:10], "payments": Payment.objects.filter(appointment__patient=patient).order_by("-created_at")[:10]})
    if doctor:
        appointments = doctor.appointments.select_related("patient", "service").order_by("appointment_time")
        return render(request, "portal/doctor.html", {"doctor": doctor, "appointments": appointments[:50], "records": doctor.medical_records.all()[:10], "prescriptions": doctor.prescriptions.all()[:10]})
    if request.user.is_superuser or request.user.is_staff:
        return redirect("admin_panel")
    if _is_staff_role(request.user):
        return redirect("reports")
    return render(request, "portal/unlinked.html")

@doctor_or_staff_required
def doctor_patients(request):
    """Shifokor faqat o'z qabullaridagi bemorlarni ko'radi; vakolatli xodimlar barcha bemorlarni ko'rishi mumkin."""
    doctor = _doctor_for(request.user)
    query = request.GET.get("q", "").strip()
    if doctor:
        patients = Patient.objects.filter(appointments__doctor=doctor).distinct()
    else:
        patients = Patient.objects.all()
    if query:
        from django.db.models import Q
        patients = patients.filter(Q(full_name__icontains=query) | Q(phone__icontains=query) | Q(email__icontains=query))
    patients = patients.order_by("full_name").prefetch_related("appointments")
    return render(request, "portal/doctor_patients.html", {"patients": patients, "query": query, "doctor": doctor})


@doctor_or_staff_required
def doctor_patient_detail(request, patient_id):
    """Bemor ma'lumotlari faqat bemorga xizmat ko'rsatgan shifokor yoki ruxsatli xodimga ko'rsatiladi."""
    doctor = _doctor_for(request.user)
    if doctor:
        patient = get_object_or_404(Patient, pk=patient_id, appointments__doctor=doctor)
        appointments = Appointment.objects.filter(patient=patient, doctor=doctor).select_related("doctor", "service").order_by("-appointment_time")
        # Bemor bilan klinik aloqasi tasdiqlangan shifokor bemorning klinik tarixini ko'rishi mumkin.
        records = patient.medical_records.all()
        prescriptions = patient.prescriptions.all()
        labs = patient.lab_results.all()
    else:
        patient = get_object_or_404(Patient, pk=patient_id)
        appointments = patient.appointments.select_related("doctor", "service").order_by("-appointment_time")
        records = patient.medical_records.all()
        prescriptions = patient.prescriptions.all()
        labs = patient.lab_results.all()
    return render(request, "portal/doctor_patient_detail.html", {
        "patient": patient, "appointments": appointments, "records": records,
        "prescriptions": prescriptions, "labs": labs,
    })


@login_required
def available_slots(request):
    """Return available appointment slots as JSON: ?doctor=ID&date=YYYY-MM-DD"""
    doctor_id, date_text = request.GET.get("doctor", ""), request.GET.get("date", "")
    try:
        doctor = Doctor.objects.get(pk=int(doctor_id), is_active=True)
        day = datetime.strptime(date_text, "%Y-%m-%d").date()
    except (ValueError, TypeError, Doctor.DoesNotExist):
        return JsonResponse({"slots": [], "error": "Shifokor yoki sana noto'g'ri."}, status=400)
    if day < timezone.localdate():
        return JsonResponse({"slots": []})
    schedule = DoctorSchedule.objects.filter(doctor=doctor, weekday=day.weekday(), is_active=True).first()
    if not schedule:
        return JsonResponse({"slots": []})
    busy = set(Appointment.objects.filter(doctor=doctor, appointment_time__date=day).exclude(status="cancelled").values_list("appointment_time", flat=True))
    slots, current = [], datetime.combine(day, schedule.start_time)
    end = datetime.combine(day, schedule.end_time)
    while current + timedelta(minutes=schedule.slot_minutes) <= end:
        aware = timezone.make_aware(current, timezone.get_current_timezone()) if settings.USE_TZ else current
        if current > datetime.combine(timezone.localdate(), timezone.localtime().time()).replace(tzinfo=None) and aware not in busy:
            slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=schedule.slot_minutes)
    return JsonResponse({"slots": slots, "doctor": doctor.full_name, "date": date_text})

@login_required
def medical_history(request):
    patient = _patient_for(request.user)
    if patient:
        return render(request, "portal/medical_history.html", {"patient": patient, "records": patient.medical_records.all(), "labs": patient.lab_results.all(), "prescriptions": patient.prescriptions.all()})
    if (not _is_staff_role(request.user) and not _doctor_for(request.user)) or (_profile(request.user) and _profile(request.user).role == "accountant"):
        return HttpResponseForbidden("Ruxsat yo'q")
    if _doctor_for(request.user):
        doctor = _doctor_for(request.user)
        patient_ids = doctor.appointments.values_list("patient_id", flat=True).distinct()
        records = MedicalRecord.objects.filter(patient_id__in=patient_ids)
        labs = LabResult.objects.filter(patient_id__in=patient_ids)
        prescriptions = Prescription.objects.filter(doctor=doctor)
    else:
        records, labs, prescriptions = MedicalRecord.objects.all(), LabResult.objects.all(), Prescription.objects.all()
    return render(request, "portal/medical_history.html", {"records": records, "labs": labs, "prescriptions": prescriptions})

@doctor_or_staff_required
def add_medical_record(request):
    form = MedicalRecordForm(request.POST or None)
    doctor = _doctor_for(request.user)
    if doctor:
        allowed_patients = Patient.objects.filter(appointments__doctor=doctor).distinct()
        form.fields["patient"].queryset = allowed_patients
        form.fields["doctor"].queryset = Doctor.objects.filter(pk=doctor.pk)
        form.fields["doctor"].initial = doctor.pk
        form.fields["appointment"].queryset = Appointment.objects.filter(doctor=doctor)
    if request.method == "POST" and form.is_valid():
        form.save(); messages.success(request, "Tibbiy tarix saqlandi."); return redirect("medical_history")
    return render(request, "portal/form.html", {"form": form, "title": "Tibbiy tarixga yozuv qo'shish"})

@staff_required
def add_lab_result(request):
    form = LabResultForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save(); messages.success(request, "Tahlil natijasi saqlandi."); return redirect("medical_history")
    return render(request, "portal/form.html", {"form": form, "title": "Tahlil natijasini qo'shish"})

@doctor_or_staff_required
def add_prescription(request):
    form = PrescriptionForm(request.POST or None)
    doctor = _doctor_for(request.user)
    if doctor:
        form.fields["patient"].queryset = Patient.objects.filter(appointments__doctor=doctor).distinct()
        form.fields["doctor"].queryset = Doctor.objects.filter(pk=doctor.pk)
        form.fields["doctor"].initial = doctor.pk
        form.fields["appointment"].queryset = Appointment.objects.filter(doctor=doctor)
    if request.method == "POST" and form.is_valid():
        form.save(); messages.success(request, "Retsept saqlandi."); return redirect("medical_history")
    return render(request, "portal/form.html", {"form": form, "title": "Retsept yozish"})


@login_required
def download_lab_attachment(request, result_id):
    result = get_object_or_404(LabResult.objects.select_related("patient"), pk=result_id)
    patient = _patient_for(request.user)
    doctor = _doctor_for(request.user)
    permitted = request.user.is_staff or request.user.is_superuser or (patient and result.patient_id == patient.id) or (doctor and result.patient.appointments.filter(doctor=doctor).exists()) or (_profile(request.user) and _profile(request.user).role in {"lab", "manager"})
    if not permitted:
        return HttpResponseForbidden("Bu faylni ko'rishga ruxsat yo'q.")
    if not result.attachment:
        raise Http404("Fayl topilmadi")
    return FileResponse(result.attachment.open("rb"), as_attachment=True, filename=result.attachment.name.rsplit("/", 1)[-1])

@login_required
@require_POST
def create_payment(request, appointment_id):
    appointment = get_object_or_404(Appointment.objects.select_related("patient", "doctor", "service"), pk=appointment_id)
    patient = _patient_for(request.user)
    if not (request.user.is_staff or request.user.is_superuser or (patient and appointment.patient_id == patient.id) or (_doctor_for(request.user) and appointment.doctor_id == _doctor_for(request.user).id)):
        return HttpResponseForbidden("Bu to'lovni ko'rishga ruxsat yo'q.")
    amount = appointment.service.price if appointment.service_id else appointment.doctor.consultation_price
    payment = Payment.objects.create(appointment=appointment, amount=amount, method=(request.POST.get("method", "click") if request.POST.get("method", "click") in dict(Payment.METHOD_CHOICES) else "click"))
    # Security: do not mark paid here. The payment provider must confirm via a signed webhook.
    messages.info(request, "To'lov so'rovi yaratildi. Haqiqiy Click/Payme to'lovi uchun provayder merchant kalitlari va imzolangan callback ulanishi kerak.")
    return redirect("portal")

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser or (_profile(u) and _profile(u).role in {"accountant", "manager"}), login_url="home")
def reports(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)
    paid = Payment.objects.filter(status="paid", paid_at__date__gte=month_start)
    context = {
        "today": today,
        "appointment_total": Appointment.objects.count(),
        "appointment_today": Appointment.objects.filter(appointment_time__date=today).count(),
        "patients_total": Patient.objects.count(),
        "doctors_total": Doctor.objects.filter(is_active=True).count(),
        "month_revenue": paid.aggregate(total=Sum("amount"))["total"] or Decimal("0"),
        "paid_count": paid.count(),
        "status_counts": Appointment.objects.values("status").annotate(total=Count("id")).order_by("status"),
        "recent_payments": Payment.objects.select_related("appointment__patient", "appointment__doctor").order_by("-created_at")[:20],
    }
    return render(request, "portal/reports.html", context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser or (_profile(u) and u.clinic_profile.role in {"accountant", "manager"}), login_url="home")
@require_POST
def mark_payment_paid(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id)
    # Only offline cash/terminal records can be manually confirmed here.
    if payment.status != "pending" or payment.method not in {"cash", "terminal", "other"}:
        messages.error(request, "Onlayn to'lov provayder tasdig'isiz qo'lda tasdiqlanmaydi.")
        return redirect("reports")
    payment.status = "paid"; payment.paid_at = timezone.now(); payment.save(update_fields=["status", "paid_at"])
    messages.success(request, "To'lov qo'lda tasdiqlandi.")
    return redirect("reports")
class DoctorScheduleForm(forms.ModelForm):
    class Meta:
        model = DoctorSchedule
        fields = [
            "doctor",
            "weekday",
            "start_time",
            "end_time",
            "slot_minutes",
            "is_active",
        ]
        widgets = {
            "start_time": forms.TimeInput(
                format="%H:%M",
                attrs={"type": "time", "class": "form-control"},
            ),
            "end_time": forms.TimeInput(
                format="%H:%M",
                attrs={"type": "time", "class": "form-control"},
            ),
        }


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff, login_url="home")
def doctor_schedules(request):
    if request.method == "POST":
        schedule_id = request.POST.get("schedule_id")

        if schedule_id:
            schedule = get_object_or_404(
                DoctorSchedule,
                pk=schedule_id,
            )
        else:
            schedule = DoctorSchedule()

        form = DoctorScheduleForm(request.POST, instance=schedule)

        if form.is_valid():
            form.save()
            messages.success(request, "Shifokor ish jadvali saqlandi.")
            return redirect("doctor_schedules")
    else:
        form = DoctorScheduleForm()

    schedules = DoctorSchedule.objects.select_related(
        "doctor"
    ).order_by("weekday", "start_time")

    return render(
        request,
        "portal/doctor_schedules.html",
        {
            "form": form,
            "schedules": schedules,
        },
    )


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff, login_url="home")
def delete_doctor_schedule(request, schedule_id):
    if request.method != "POST":
        return redirect("doctor_schedules")

    schedule = get_object_or_404(DoctorSchedule, pk=schedule_id)
    schedule.delete()

    messages.success(request, "Ish jadvali o‘chirildi.")
    return redirect("doctor_schedules")