import os
import json
import base64
import urllib.parse
import urllib.request
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from appointments.models import Appointment, ReminderLog

class Command(BaseCommand):
    help = "Yaqin 24 soat ichidagi qabullar uchun Twilio orqali SMS eslatma yuboradi."

    def handle(self, *args, **options):
        sid, token, sender = (os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"), os.getenv("TWILIO_FROM_NUMBER"))
        if not all([sid, token, sender]):
            raise CommandError("SMS yuborish uchun TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN va TWILIO_FROM_NUMBER muhit o'zgaruvchilarini sozlang.")
        now = timezone.now(); end = now + timedelta(hours=24)
        qs = Appointment.objects.filter(appointment_time__gte=now, appointment_time__lte=end, status__in=["pending", "scheduled"]).select_related("doctor", "patient")
        sent = 0
        for appointment in qs:
            phone = appointment.patient.phone
            if not phone: continue
            if appointment.reminder_logs.filter(status="sent").exists(): continue
            when = timezone.localtime(appointment.appointment_time).strftime("%d.%m.%Y %H:%M")
            body = f"ShifoCare eslatmasi: {when} da {appointment.doctor.full_name} qabuliga yozilgansiz."
            log = ReminderLog.objects.create(appointment=appointment, phone=phone, message=body, status="sending")
            url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
            data = urllib.parse.urlencode({"To": phone, "From": sender, "Body": body}).encode()
            request = urllib.request.Request(url, data=data)
            auth = base64.b64encode(f"{sid}:{token}".encode()).decode()
            request.add_header("Authorization", f"Basic {auth}")
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    response_body = response.read().decode()
                    log.status = "sent"; log.provider_response = response_body; log.sent_at = timezone.now(); log.save()
                    sent += 1
            except Exception as exc:
                log.status = "failed"; log.provider_response = str(exc); log.save()
                self.stderr.write(f"SMS xatosi ({phone}): {exc}")
        self.stdout.write(self.style.SUCCESS(f"Yuborilgan SMS: {sent}"))
