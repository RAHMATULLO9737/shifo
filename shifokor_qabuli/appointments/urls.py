from django.urls import path, include
from . import views
from . import feature_views as features

urlpatterns = [
    path("", views.home, name="home"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("ro-yxatdan-otish/", features.register_patient, name="register_patient"),
    path("kabinet/", features.portal, name="portal"),
    path("admin-panel/", features.admin_panel, name="admin_panel"),
    path("shifokor-paneli/", features.doctor_panel, name="doctor_panel"),
    path("bemor-paneli/", features.patient_panel, name="patient_panel"),
    path("shifokor/bemorlar/", features.doctor_patients, name="doctor_patients"),
    path("shifokor/bemorlar/<int:patient_id>/", features.doctor_patient_detail, name="doctor_patient_detail"),
    path("tibbiy-tarix/", features.medical_history, name="medical_history"),
    path("tahlil-fayli/<int:result_id>/", features.download_lab_attachment, name="download_lab_attachment"),
    path("tibbiy-tarix/qoshish/", features.add_medical_record, name="add_medical_record"),
    path("tahlil-natijasi/qoshish/", features.add_lab_result, name="add_lab_result"),
    path("retsept/qoshish/", features.add_prescription, name="add_prescription"),
    path("api/qabul-vaqtlari/", features.available_slots, name="available_slots"),
    path("tolov/<int:appointment_id>/", features.create_payment, name="create_payment"),
    path("hisobotlar/", features.reports, name="reports"),
    path("tolov/<int:payment_id>/tasdiqlash/", features.mark_payment_paid, name="mark_payment_paid"),
    path("shifokorlar/", views.doctors, name="doctors"),
    path("shifokor-qoshish/", views.add_doctor, name="add_doctor"),
    path("bemorlar/", views.patients, name="patients"),
    path("xizmatlar/", views.services, name="services"),
    path("qabullar/", views.appointments_list, name="appointments_list"),
    path("qabullar/<int:pk>/bekor-qilish/", views.cancel_appointment, name="cancel_appointment"),
    path("qabul-belgilash/", views.book_appointment, name="book_appointment"),
    path(
    "ish-jadvali/",
    features.doctor_schedules,
    name="doctor_schedules",
),
path(
    "ish-jadvali/<int:schedule_id>/ochirish/",
    features.delete_doctor_schedule,
    name="delete_doctor_schedule",
),
]
