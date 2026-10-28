import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('appointments', '0002_seed_catalogs'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.AddField(
            model_name='doctor', name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='doctor_profile', to=settings.AUTH_USER_MODEL, verbose_name='Tizim foydalanuvchisi'),
        ),
        migrations.AddField(
            model_name='patient', name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='patient_profile', to=settings.AUTH_USER_MODEL, verbose_name='Tizim foydalanuvchisi'),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('patient', 'Bemor'), ('doctor', 'Shifokor'), ('reception', 'Registratura'), ('accountant', 'Hisobchi'), ('lab', 'Laboratoriya'), ('manager', 'Menejer')], default='patient', max_length=20, verbose_name='Rol')),
                ('phone', models.CharField(blank=True, max_length=30, verbose_name='Telefon')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='clinic_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Foydalanuvchi roli', 'verbose_name_plural': 'Foydalanuvchi rollari'},
        ),
        migrations.CreateModel(
            name='MedicalRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('diagnosis', models.CharField(max_length=250, verbose_name='Tashxis')),
                ('notes', models.TextField(blank=True, verbose_name='Tibbiy qaydlar')),
                ('recorded_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Sana')),
                ('appointment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='medical_records', to='appointments.appointment', verbose_name='Qabul')),
                ('doctor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='medical_records', to='appointments.doctor', verbose_name='Shifokor')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='medical_records', to='appointments.patient', verbose_name='Bemor')),
            ],
            options={'verbose_name': 'Tibbiy tarix yozuvi', 'verbose_name_plural': 'Tibbiy tarix', 'ordering': ['-recorded_at']},
        ),
        migrations.CreateModel(
            name='LabResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('test_name', models.CharField(max_length=180, verbose_name='Tahlil nomi')),
                ('result', models.TextField(verbose_name='Natija')),
                ('reference_range', models.CharField(blank=True, max_length=180, verbose_name="Me'yor oralig'i")),
                ('attachment', models.FileField(blank=True, upload_to='lab_results/%Y/%m/', verbose_name='Natija fayli')),
                ('result_date', models.DateField(default=django.utils.timezone.localdate, verbose_name='Natija sanasi')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ordered_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='appointments.doctor', verbose_name="Yo'llanma bergan shifokor")),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lab_results', to='appointments.patient', verbose_name='Bemor')),
            ],
            options={'verbose_name': 'Laboratoriya natijasi', 'verbose_name_plural': 'Laboratoriya natijalari', 'ordering': ['-result_date', 'test_name']},
        ),
        migrations.CreateModel(
            name='Prescription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('medication', models.CharField(max_length=180, verbose_name='Dori nomi')),
                ('dosage', models.CharField(max_length=180, verbose_name='Dozasi')),
                ('instructions', models.TextField(verbose_name="Qo'llash ko'rsatmasi")),
                ('issued_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Berilgan sana')),
                ('appointment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='appointments.appointment', verbose_name='Qabul')),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='prescriptions', to='appointments.doctor', verbose_name='Shifokor')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prescriptions', to='appointments.patient', verbose_name='Bemor')),
            ],
            options={'verbose_name': 'Retsept', 'verbose_name_plural': 'Retseptlar', 'ordering': ['-issued_at']},
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12, verbose_name="Summa (so'm)")),
                ('method', models.CharField(choices=[('click', 'Click'), ('payme', 'Payme'), ('cash', 'Naqd'), ('terminal', 'Terminal'), ('other', 'Boshqa')], default='click', max_length=20, verbose_name='Usul')),
                ('status', models.CharField(choices=[('pending', "To'lov kutilmoqda"), ('paid', "To'langan"), ('failed', 'Muvaffaqiyatsiz'), ('refunded', 'Qaytarilgan')], default='pending', max_length=20, verbose_name='Holati')),
                ('transaction_id', models.CharField(blank=True, db_index=True, max_length=160, verbose_name='Tranzaksiya ID')),
                ('paid_at', models.DateTimeField(blank=True, null=True, verbose_name="To'langan vaqt")),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('appointment', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='payments', to='appointments.appointment', verbose_name='Qabul')),
            ],
            options={'verbose_name': "To'lov", 'verbose_name_plural': "To'lovlar", 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='ReminderLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(max_length=30)),
                ('message', models.TextField()),
                ('status', models.CharField(default='queued', max_length=30)),
                ('provider_response', models.TextField(blank=True)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('appointment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reminder_logs', to='appointments.appointment')),
            ],
            options={'verbose_name': 'SMS eslatma jurnali', 'verbose_name_plural': 'SMS eslatmalar jurnali', 'ordering': ['-created_at']},
        ),
    ]
