# Initial database schema for ShifoCare.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True, verbose_name='Xizmat nomi')),
                ('description', models.TextField(blank=True, verbose_name='Tavsif')),
                ('price', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Narxi (so'm)")),
                ('duration_minutes', models.PositiveSmallIntegerField(default=30, verbose_name='Davomiyligi (daqiqa)')),
                ('is_active', models.BooleanField(default=True, verbose_name='Faol')),
            ],
            options={'verbose_name': 'Tibbiy xizmat', 'verbose_name_plural': 'Tibbiy xizmatlar', 'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Specialty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True, verbose_name='Mutaxassislik nomi')),
                ('description', models.TextField(blank=True, verbose_name='Tavsif')),
                ('is_active', models.BooleanField(default=True, verbose_name='Faol')),
            ],
            options={'verbose_name': 'Mutaxassislik', 'verbose_name_plural': 'Mutaxassisliklar', 'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=150, verbose_name='F.I.Sh.')),
                ('birth_date', models.DateField(blank=True, null=True, verbose_name="Tug'ilgan sana")),
                ('gender', models.CharField(blank=True, choices=[('', "Ko'rsatilmagan"), ('M', 'Erkak'), ('F', 'Ayol')], max_length=1, verbose_name='Jinsi')),
                ('phone', models.CharField(max_length=30, verbose_name='Telefon')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='Email')),
                ('address', models.CharField(blank=True, max_length=250, verbose_name='Manzil')),
                ('notes', models.TextField(blank=True, verbose_name='Ichki izoh')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name="Ro'yxatdan o'tgan vaqt")),
            ],
            options={'verbose_name': 'Bemor', 'verbose_name_plural': 'Bemorlar', 'ordering': ['full_name']},
        ),
        migrations.CreateModel(
            name='Doctor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=150, verbose_name='F.I.Sh.')),
                ('specialty_text', models.CharField(blank=True, help_text="Ro'yxatda yo'q mutaxassislik bo'lsa yozing", max_length=120, verbose_name='Mutaxassislik (boshqa)')),
                ('phone', models.CharField(blank=True, max_length=30, verbose_name='Telefon')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='Email')),
                ('room', models.CharField(blank=True, max_length=30, verbose_name='Xona')),
                ('experience_years', models.PositiveSmallIntegerField(default=0, verbose_name='Tajriba (yil)')),
                ('consultation_price', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Qabul narxi (so'm)")),
                ('bio', models.TextField(blank=True, verbose_name='Shifokor haqida')),
                ('is_active', models.BooleanField(default=True, verbose_name='Faol')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name="Qo'shilgan vaqt")),
                ('specialty', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='doctors', to='appointments.specialty', verbose_name='Mutaxassisligi')),
            ],
            options={'verbose_name': 'Shifokor', 'verbose_name_plural': 'Shifokorlar', 'ordering': ['full_name']},
        ),
        migrations.CreateModel(
            name='DoctorSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekday', models.PositiveSmallIntegerField(choices=[(0, 'Dushanba'), (1, 'Seshanba'), (2, 'Chorshanba'), (3, 'Payshanba'), (4, 'Juma'), (5, 'Shanba'), (6, 'Yakshanba')], verbose_name='Hafta kuni')),
                ('start_time', models.TimeField(verbose_name='Ish boshlanishi')),
                ('end_time', models.TimeField(verbose_name='Ish tugashi')),
                ('slot_minutes', models.PositiveSmallIntegerField(default=30, verbose_name='Qabul oralig\'i (daqiqa)')),
                ('is_active', models.BooleanField(default=True, verbose_name='Faol')),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedules', to='appointments.doctor', verbose_name='Shifokor')),
            ],
            options={'verbose_name': 'Shifokor ish jadvali', 'verbose_name_plural': 'Shifokor ish jadvallari', 'ordering': ['weekday', 'start_time'], 'unique_together': {('doctor', 'weekday')}},
        ),
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appointment_time', models.DateTimeField(verbose_name='Qabul sanasi va vaqti')),
                ('reason', models.CharField(blank=True, max_length=250, verbose_name='Murojaat sababi')),
                ('status', models.CharField(choices=[('pending', 'Kutilmoqda'), ('scheduled', 'Tasdiqlangan'), ('completed', 'Yakunlangan'), ('cancelled', 'Bekor qilingan')], default='pending', max_length=20, verbose_name='Holati')),
                ('internal_notes', models.TextField(blank=True, verbose_name='Xodim izohi')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan vaqt')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilangan vaqt')),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='appointments', to='appointments.doctor', verbose_name='Shifokor')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='appointments', to='appointments.patient', verbose_name='Bemor')),
                ('service', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appointments', to='appointments.service', verbose_name='Xizmat')),
            ],
            options={'verbose_name': 'Qabul', 'verbose_name_plural': 'Qabullar', 'ordering': ['appointment_time']},
        ),
        migrations.AddIndex(
            model_name='appointment',
            index=models.Index(fields=['appointment_time', 'status'], name='appoint_time_status_idx'),
        ),
    ]
