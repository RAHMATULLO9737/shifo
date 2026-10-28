from django import forms
from .models import Patient, Appointment, Doctor


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class PatientForm(StyledModelForm):
    class Meta:
        model = Patient
        fields = ["full_name", "birth_date", "gender", "phone", "email", "address", "notes"]
        widgets = {"birth_date": forms.DateInput(attrs={"type": "date"}), "notes": forms.Textarea(attrs={"rows": 3}), "address": forms.TextInput(attrs={"placeholder": "Shahar, ko'cha, uy"})}


class DoctorForm(StyledModelForm):
    class Meta:
        model = Doctor
        fields = ["full_name", "specialty", "specialty_text", "phone", "email", "room", "experience_years", "consultation_price", "bio", "is_active"]
        widgets = {"bio": forms.Textarea(attrs={"rows": 3})}


class AppointmentForm(StyledModelForm):
    class Meta:
        model = Appointment
        fields = ["doctor", "patient", "service", "appointment_time", "reason"]
        widgets = {"appointment_time": forms.DateTimeInput(format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local", "step": "300"}), "reason": forms.TextInput(attrs={"placeholder": "Masalan: umumiy ko'rik"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["doctor"].queryset = Doctor.objects.filter(is_active=True).select_related("specialty")
        self.fields["service"].queryset = self.fields["service"].queryset.filter(is_active=True)
        self.fields["service"].required = False

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

class PatientRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    full_name = forms.CharField(max_length=150, label="F.I.Sh.")
    phone = forms.CharField(max_length=30, label="Telefon")

    class Meta:
        model = User
        fields = ("username", "full_name", "email", "phone", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

class MedicalRecordForm(StyledModelForm):
    class Meta:
        from .models import MedicalRecord
        model = MedicalRecord
        fields = ["patient", "doctor", "appointment", "diagnosis", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 4})}

class LabResultForm(StyledModelForm):
    class Meta:
        from .models import LabResult
        model = LabResult
        fields = ["patient", "ordered_by", "test_name", "result", "reference_range", "attachment", "result_date"]
        widgets = {"result": forms.Textarea(attrs={"rows": 4}), "result_date": forms.DateInput(attrs={"type": "date"})}

class PrescriptionForm(StyledModelForm):
    class Meta:
        from .models import Prescription
        model = Prescription
        fields = ["patient", "doctor", "appointment", "medication", "dosage", "instructions"]
        widgets = {"instructions": forms.Textarea(attrs={"rows": 4})}
