from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Doctor, Patient, Appointment, Specialty, Service
from .forms import PatientForm, AppointmentForm, DoctorForm


# =====================================================
# XODIMLAR UCHUN RUXSATNI TEKSHIRISH
# =====================================================

def _staff_user(user):
    """
    Admin yoki ruxsat berilgan xodim ekanligini tekshiradi.
    """
    if not user.is_authenticated:
        return False

    if user.is_staff or user.is_superuser:
        return True

    try:
        profile = user.clinic_profile
        return profile.role in {
            "reception",
            "accountant",
            "lab",
            "manager",
        }
    except Exception:
        return False


# =====================================================
# BOSH SAHIFA
# =====================================================

def home(request):
    today = timezone.localdate()

    today_appointments = Appointment.objects.filter(
        appointment_time__date=today
    ).exclude(status="cancelled")

    context = {
        "doctor_count": Doctor.objects.filter(
            is_active=True
        ).count(),

        "patient_count": Patient.objects.count(),

        "today_count": today_appointments.count(),

        "pending_count": Appointment.objects.filter(
            status="pending"
        ).count(),

        "upcoming": Appointment.objects.filter(
            appointment_time__gte=timezone.now()
        ).exclude(
            status="cancelled"
        ).select_related(
            "doctor",
            "patient",
            "doctor__specialty",
        ).order_by(
            "appointment_time"
        )[:8],

        "service_count": Service.objects.filter(
            is_active=True
        ).count(),
    }

    return render(
        request,
        "appointments/home.html",
        context,
    )


# =====================================================
# SHIFOKORLAR RO'YXATI
# =====================================================

def doctors(request):
    query = request.GET.get("q", "").strip()
    specialty_id = request.GET.get("specialty", "")

    items = Doctor.objects.filter(
        is_active=True
    ).select_related("specialty")

    if query:
        items = items.filter(
            Q(full_name__icontains=query)
            | Q(specialty__name__icontains=query)
            | Q(specialty_text__icontains=query)
        )

    if specialty_id.isdigit():
        items = items.filter(
            specialty_id=int(specialty_id)
        )

    context = {
        "doctors": items,
        "query": query,
        "specialties": Specialty.objects.filter(
            is_active=True
        ),
        "selected_specialty": specialty_id,
    }

    return render(
        request,
        "appointments/doctors.html",
        context,
    )


# =====================================================
# BEMORLAR RO'YXATI
# =====================================================

@login_required
@user_passes_test(_staff_user, login_url="home")
def patients(request):
    query = request.GET.get("q", "").strip()

    form = PatientForm(
        request.POST or None
    )

    if request.method == "POST":
        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Bemor muvaffaqiyatli qo'shildi."
            )

            return redirect("patients")

    items = Patient.objects.all().order_by(
        "full_name"
    )

    if query:
        items = items.filter(
            Q(full_name__icontains=query)
            | Q(phone__icontains=query)
            | Q(email__icontains=query)
        )

    page = Paginator(
        items,
        15
    ).get_page(
        request.GET.get("page")
    )

    context = {
        "patients": page,
        "form": form,
        "query": query,
    }

    return render(
        request,
        "appointments/patients.html",
        context,
    )


# =====================================================
# YANGI SHIFOKOR QO'SHISH
# =====================================================

@login_required
@user_passes_test(_staff_user, login_url="home")
def add_doctor(request):
    form = DoctorForm(
        request.POST or None
    )

    if request.method == "POST":
        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Shifokor muvaffaqiyatli qo'shildi."
            )

            return redirect("doctors")

    return render(
        request,
        "appointments/doctor_form.html",
        {"form": form},
    )


# =====================================================
# QABULGA YOZILISH
# =====================================================

@login_required
def book_appointment(request):
    """
    Foydalanuvchi tizimga kirganidan keyin
    qabulga yozilish imkoniyatini beradi.
    """

    form = AppointmentForm(
        request.POST or None
    )

    # Foydalanuvchining bemor profilini aniqlaymiz.
    try:
        patient_profile = request.user.patient_profile
    except Patient.DoesNotExist:
        patient_profile = None

    # Bemor faqat o'z nomidan qabulga yoziladi.
    if patient_profile:
        if "patient" in form.fields:
            form.fields["patient"].queryset = (
                Patient.objects.filter(
                    pk=patient_profile.pk
                )
            )

            form.fields["patient"].initial = (
                patient_profile.pk
            )

            form.fields["patient"].widget = (
                forms.HiddenInput()
            )

    if request.method == "POST":
        if form.is_valid():
            appointment = form.save(
                commit=False
            )

            # Bemor profiliga ega foydalanuvchi
            # boshqa bemor nomidan yozila olmaydi.
            if patient_profile:
                appointment.patient = patient_profile

            try:
                appointment.full_clean()
                appointment.save()

                messages.success(
                    request,
                    "Qabulga yozilish so'rovingiz saqlandi."
                )

                # Bemor o'z kabinetiga o'tadi.
                if patient_profile:
                    return redirect("patient_panel")

                # Xodim qabul ro'yxatiga o'tadi.
                if _staff_user(request.user):
                    return redirect("appointments_list")

                # Boshqa foydalanuvchi kabinetga o'tadi.
                return redirect("portal")

            except ValidationError as exc:
                if hasattr(exc, "message_dict"):
                    for field_errors in exc.message_dict.values():
                        for error in field_errors:
                            form.add_error(
                                None,
                                error
                            )
                else:
                    for error in exc.messages:
                        form.add_error(
                            None,
                            error
                        )

            except Exception:
                messages.error(
                    request,
                    "Qabulni saqlashda xatolik yuz berdi. "
                    "Ma'lumotlarni tekshirib, qayta urinib ko'ring."
                )

    return render(
        request,
        "appointments/book.html",
        {"form": form},
    )


# =====================================================
# QABULLAR RO'YXATI
# =====================================================

@login_required
@user_passes_test(_staff_user, login_url="home")
def appointments_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")

    items = Appointment.objects.select_related(
        "doctor",
        "patient",
        "service",
        "doctor__specialty",
    ).order_by(
        "-appointment_time"
    )

    if query:
        items = items.filter(
            Q(patient__full_name__icontains=query)
            | Q(patient__phone__icontains=query)
            | Q(doctor__full_name__icontains=query)
        )

    if status in dict(Appointment.STATUS_CHOICES):
        items = items.filter(
            status=status
        )

    page = Paginator(
        items,
        20
    ).get_page(
        request.GET.get("page")
    )

    context = {
        "appointments": page,
        "query": query,
        "selected_status": status,
        "statuses": Appointment.STATUS_CHOICES,
    }

    return render(
        request,
        "appointments/appointments.html",
        context,
    )


# =====================================================
# QABULNI BEKOR QILISH
# =====================================================

@login_required
@user_passes_test(_staff_user, login_url="home")
@require_POST
def cancel_appointment(request, pk):
    appointment = get_object_or_404(
        Appointment,
        pk=pk
    )

    if appointment.status not in (
        "completed",
        "cancelled",
    ):
        appointment.status = "cancelled"

        appointment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        messages.success(
            request,
            "Qabul bekor qilindi."
        )

    else:
        messages.warning(
            request,
            "Yakunlangan yoki bekor qilingan "
            "qabul holatini o'zgartirib bo'lmaydi."
        )

    return redirect(
        "appointments_list"
    )


# =====================================================
# XIZMATLAR RO'YXATI
# =====================================================

def services(request):
    items = Service.objects.filter(
        is_active=True
    )

    return render(
        request,
        "appointments/services.html",
        {"services": items},
    )


# =====================================================
# SHIFOKOR PANELI
# =====================================================

@login_required
def doctor_panel(request):
    """
    Shifokor faqat o'ziga tegishli qabullarni ko'radi.
    """

    try:
        doctor = request.user.doctor_profile
    except Doctor.DoesNotExist:
        messages.error(
            request,
            "Sizga shifokor profili biriktirilmagan."
        )
        return redirect("portal")

    appointments = Appointment.objects.filter(
        doctor=doctor
    ).select_related(
        "patient",
        "service",
    ).order_by(
        "-appointment_time"
    )

    context = {
        "doctor": doctor,
        "appointments": appointments,
        "appointment_count": appointments.count(),
        "pending_count": appointments.filter(
            status="pending"
        ).count(),
    }

    return render(
        request,
        "appointments/doctor_panel.html",
        context,
    )