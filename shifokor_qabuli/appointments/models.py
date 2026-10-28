from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings


class Specialty(models.Model):
    name = models.CharField("Mutaxassislik nomi", max_length=120, unique=True)
    description = models.TextField("Tavsif", blank=True)
    is_active = models.BooleanField("Faol", default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Mutaxassislik"
        verbose_name_plural = "Mutaxassisliklar"

    def __str__(self):
        return self.name


class Service(models.Model):
    name = models.CharField("Xizmat nomi", max_length=150, unique=True)
    description = models.TextField("Tavsif", blank=True)
    price = models.DecimalField("Narxi (so'm)", max_digits=12, decimal_places=2, default=0)
    duration_minutes = models.PositiveSmallIntegerField("Davomiyligi (daqiqa)", default=30)
    is_active = models.BooleanField("Faol", default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Tibbiy xizmat"
        verbose_name_plural = "Tibbiy xizmatlar"

    def __str__(self):
        return self.name


class Doctor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="doctor_profile", verbose_name="Tizim foydalanuvchisi")
    full_name = models.CharField("F.I.Sh.", max_length=150)
    specialty = models.ForeignKey(Specialty, on_delete=models.PROTECT, verbose_name="Mutaxassisligi", related_name="doctors", null=True, blank=True)
    specialty_text = models.CharField("Mutaxassislik (boshqa)", max_length=120, blank=True, help_text="Ro'yxatda yo'q mutaxassislik bo'lsa yozing")
    phone = models.CharField("Telefon", max_length=30, blank=True)
    email = models.EmailField("Email", blank=True)
    room = models.CharField("Xona", max_length=30, blank=True)
    experience_years = models.PositiveSmallIntegerField("Tajriba (yil)", default=0)
    consultation_price = models.DecimalField("Qabul narxi (so'm)", max_digits=12, decimal_places=2, default=0)
    bio = models.TextField("Shifokor haqida", blank=True)
    is_active = models.BooleanField("Faol", default=True)
    created_at = models.DateTimeField("Qo'shilgan vaqt", auto_now_add=True)

    class Meta:
        ordering = ["full_name"]
        verbose_name = "Shifokor"
        verbose_name_plural = "Shifokorlar"

    @property
    def specialty_name(self):
        return self.specialty.name if self.specialty_id else (self.specialty_text or "Umumiy amaliyot")

    def __str__(self):
        return f"{self.full_name} — {self.specialty_name}"


class DoctorSchedule(models.Model):
    WEEKDAYS = [(0, "Dushanba"), (1, "Seshanba"), (2, "Chorshanba"), (3, "Payshanba"), (4, "Juma"), (5, "Shanba"), (6, "Yakshanba")]
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="schedules", verbose_name="Shifokor")
    weekday = models.PositiveSmallIntegerField("Hafta kuni", choices=WEEKDAYS)
    start_time = models.TimeField("Ish boshlanishi")
    end_time = models.TimeField("Ish tugashi")
    slot_minutes = models.PositiveSmallIntegerField("Qabul oralig'i (daqiqa)", default=30)
    is_active = models.BooleanField("Faol", default=True)

    class Meta:
        ordering = ["weekday", "start_time"]
        unique_together = [("doctor", "weekday")]
        verbose_name = "Shifokor ish jadvali"
        verbose_name_plural = "Shifokor ish jadvallari"

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({"end_time": "Ish tugash vaqti boshlanish vaqtidan keyin bo'lishi kerak."})
        if self.slot_minutes < 5:
            raise ValidationError({"slot_minutes": "Qabul oralig'i kamida 5 daqiqa bo'lishi kerak."})

    def __str__(self):
        return f"{self.doctor} — {self.get_weekday_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}"


class Patient(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="patient_profile", verbose_name="Tizim foydalanuvchisi")
    GENDER_CHOICES = [("", "Ko'rsatilmagan"), ("M", "Erkak"), ("F", "Ayol")]
    full_name = models.CharField("F.I.Sh.", max_length=150)
    birth_date = models.DateField("Tug'ilgan sana", null=True, blank=True)
    gender = models.CharField("Jinsi", max_length=1, choices=GENDER_CHOICES, blank=True)
    phone = models.CharField("Telefon", max_length=30)
    email = models.EmailField("Email", blank=True)
    address = models.CharField("Manzil", max_length=250, blank=True)
    notes = models.TextField("Ichki izoh", blank=True)
    created_at = models.DateTimeField("Ro'yxatdan o'tgan vaqt", auto_now_add=True)

    class Meta:
        ordering = ["full_name"]
        verbose_name = "Bemor"
        verbose_name_plural = "Bemorlar"

    def __str__(self):
        return f"{self.full_name} ({self.phone})"


class Appointment(models.Model):
    STATUS_CHOICES = [("pending", "Kutilmoqda"), ("scheduled", "Tasdiqlangan"), ("completed", "Yakunlangan"), ("cancelled", "Bekor qilingan")]
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, verbose_name="Shifokor", related_name="appointments")
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, verbose_name="Bemor", related_name="appointments")
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, verbose_name="Xizmat", null=True, blank=True, related_name="appointments")
    appointment_time = models.DateTimeField("Qabul sanasi va vaqti")
    reason = models.CharField("Murojaat sababi", max_length=250, blank=True)
    status = models.CharField("Holati", max_length=20, choices=STATUS_CHOICES, default="pending")
    internal_notes = models.TextField("Xodim izohi", blank=True)
    created_at = models.DateTimeField("Yaratilgan vaqt", auto_now_add=True)
    updated_at = models.DateTimeField("Yangilangan vaqt", auto_now=True)

    class Meta:
        ordering = ["appointment_time"]
        verbose_name = "Qabul"
        verbose_name_plural = "Qabullar"
        indexes = [models.Index(fields=["appointment_time", "status"], name="appoint_time_status_idx")]

    def clean(self):
        errors = {}
        if self.appointment_time and self.appointment_time < timezone.now() and not self.pk:
            errors["appointment_time"] = "O'tgan vaqtga qabul belgilab bo'lmaydi."
        if self.doctor_id and not self.doctor.is_active and self.status != "cancelled":
            errors["doctor"] = "Faol bo'lmagan shifokorga qabul belgilab bo'lmaydi."
        if self.doctor_id and self.appointment_time and self.status != "cancelled":
            conflict = Appointment.objects.filter(doctor_id=self.doctor_id, appointment_time=self.appointment_time).exclude(status="cancelled")
            if self.pk:
                conflict = conflict.exclude(pk=self.pk)
            if conflict.exists():
                errors["appointment_time"] = "Bu shifokor uchun ushbu vaqtda qabul allaqachon belgilangan."
            # If working hours are configured, validate the appointment against them.
            if not errors.get("appointment_time"):
                local_dt = timezone.localtime(self.appointment_time) if timezone.is_aware(self.appointment_time) else self.appointment_time
                schedules = DoctorSchedule.objects.filter(doctor_id=self.doctor_id, is_active=True)
                if schedules.exists():
                    schedule = schedules.filter(weekday=local_dt.weekday()).first()
                    if not schedule:
                        errors["appointment_time"] = "Shifokor tanlangan hafta kuni ishlamaydi."
                    elif not (schedule.start_time <= local_dt.time().replace(tzinfo=None) < schedule.end_time):
                        errors["appointment_time"] = f"Qabul vaqti shifokorning ish vaqtida bo'lishi kerak: {schedule.start_time:%H:%M}–{schedule.end_time:%H:%M}."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.patient} — {self.doctor} — {self.appointment_time:%Y-%m-%d %H:%M}"


class UserProfile(models.Model):
    ROLE_CHOICES = [("patient", "Bemor"), ("doctor", "Shifokor"), ("reception", "Registratura"), ("accountant", "Hisobchi"), ("lab", "Laboratoriya"), ("manager", "Menejer")]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="clinic_profile")
    role = models.CharField("Rol", max_length=20, choices=ROLE_CHOICES, default="patient")
    phone = models.CharField("Telefon", max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Foydalanuvchi roli"
        verbose_name_plural = "Foydalanuvchi rollari"

    def __str__(self):
        return f"{self.user.username} — {self.get_role_display()}"


class MedicalRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="medical_records", verbose_name="Bemor")
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name="medical_records", verbose_name="Shifokor")
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name="medical_records", verbose_name="Qabul")
    diagnosis = models.CharField("Tashxis", max_length=250)
    notes = models.TextField("Tibbiy qaydlar", blank=True)
    recorded_at = models.DateTimeField("Sana", default=timezone.now)

    class Meta:
        ordering = ["-recorded_at"]
        verbose_name = "Tibbiy tarix yozuvi"
        verbose_name_plural = "Tibbiy tarix"

    def __str__(self):
        return f"{self.patient} — {self.diagnosis}"


class LabResult(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="lab_results", verbose_name="Bemor")
    ordered_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Yo'llanma bergan shifokor")
    test_name = models.CharField("Tahlil nomi", max_length=180)
    result = models.TextField("Natija")
    reference_range = models.CharField("Me'yor oralig'i", max_length=180, blank=True)
    attachment = models.FileField("Natija fayli", upload_to="lab_results/%Y/%m/", blank=True)
    result_date = models.DateField("Natija sanasi", default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-result_date", "test_name"]
        verbose_name = "Laboratoriya natijasi"
        verbose_name_plural = "Laboratoriya natijalari"

    def __str__(self):
        return f"{self.patient} — {self.test_name}"


class Prescription(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="prescriptions", verbose_name="Bemor")
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, related_name="prescriptions", verbose_name="Shifokor")
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Qabul")
    medication = models.CharField("Dori nomi", max_length=180)
    dosage = models.CharField("Dozasi", max_length=180)
    instructions = models.TextField("Qo'llash ko'rsatmasi")
    issued_at = models.DateTimeField("Berilgan sana", default=timezone.now)

    class Meta:
        ordering = ["-issued_at"]
        verbose_name = "Retsept"
        verbose_name_plural = "Retseptlar"

    def __str__(self):
        return f"{self.patient} — {self.medication}"


class Payment(models.Model):
    STATUS_CHOICES = [("pending", "To'lov kutilmoqda"), ("paid", "To'langan"), ("failed", "Muvaffaqiyatsiz"), ("refunded", "Qaytarilgan")]
    METHOD_CHOICES = [("click", "Click"), ("payme", "Payme"), ("cash", "Naqd"), ("terminal", "Terminal"), ("other", "Boshqa")]
    appointment = models.ForeignKey(Appointment, on_delete=models.PROTECT, related_name="payments", verbose_name="Qabul")
    amount = models.DecimalField("Summa (so'm)", max_digits=12, decimal_places=2)
    method = models.CharField("Usul", max_length=20, choices=METHOD_CHOICES, default="click")
    status = models.CharField("Holati", max_length=20, choices=STATUS_CHOICES, default="pending")
    transaction_id = models.CharField("Tranzaksiya ID", max_length=160, blank=True, db_index=True)
    paid_at = models.DateTimeField("To'langan vaqt", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"

    def __str__(self):
        return f"{self.appointment} — {self.amount} so'm ({self.get_status_display()})"


class ReminderLog(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name="reminder_logs")
    phone = models.CharField(max_length=30)
    message = models.TextField()
    status = models.CharField(max_length=30, default="queued")
    provider_response = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "SMS eslatma jurnali"
        verbose_name_plural = "SMS eslatmalar jurnali"

    def __str__(self):
        return f"{self.phone} — {self.status}"
