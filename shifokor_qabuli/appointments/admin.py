from django.contrib import admin
from .models import Doctor, Patient, Appointment, Specialty, Service, DoctorSchedule

admin.site.site_header = "ShifoCare — boshqaruv paneli"
admin.site.site_title = "ShifoCare Admin"
admin.site.index_title = "Klinika boshqaruvi"

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    list_editable = ("is_active",)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "duration_minutes", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    list_editable = ("price", "is_active")

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "specialty", "specialty_text", "phone", "room", "is_active")
    list_filter = ("specialty", "is_active")
    search_fields = ("full_name", "specialty__name", "specialty_text", "phone", "email")
    list_editable = ("is_active",)

@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ("doctor", "weekday", "start_time", "end_time", "slot_minutes", "is_active")
    list_filter = ("weekday", "is_active", "doctor")
    search_fields = ("doctor__full_name",)

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "birth_date", "gender", "created_at")
    search_fields = ("full_name", "phone", "email")
    list_filter = ("gender", "created_at")
    readonly_fields = ("created_at",)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("appointment_time", "doctor", "patient", "service", "status")
    list_filter = ("status", "doctor", "service", "appointment_time")
    search_fields = ("doctor__full_name", "patient__full_name", "patient__phone")
    date_hierarchy = "appointment_time"
    list_select_related = ("doctor", "patient", "service")
    readonly_fields = ("created_at", "updated_at")

from .models import UserProfile, MedicalRecord, LabResult, Prescription, Payment, ReminderLog

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "phone", "created_at")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email", "phone")

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "diagnosis", "recorded_at")
    list_filter = ("recorded_at", "doctor")
    search_fields = ("patient__full_name", "diagnosis", "notes")

@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ("patient", "test_name", "result_date", "ordered_by")
    list_filter = ("result_date",)
    search_fields = ("patient__full_name", "test_name", "result")

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "medication", "issued_at")
    list_filter = ("issued_at", "doctor")
    search_fields = ("patient__full_name", "medication", "instructions")

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("appointment", "amount", "method", "status", "created_at", "paid_at")
    list_filter = ("status", "method", "created_at")
    search_fields = ("transaction_id", "appointment__patient__full_name")
    readonly_fields = ("created_at",)

@admin.register(ReminderLog)
class ReminderLogAdmin(admin.ModelAdmin):
    list_display = ("appointment", "phone", "status", "sent_at", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("phone", "message")
