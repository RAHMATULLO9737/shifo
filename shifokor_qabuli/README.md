# ShifoCare — klinika boshqaruv tizimi

Django asosidagi shifokor qabuli, bemor kabineti va klinika boshqaruvi loyihasi. Dastlabki loyihaning tuzilmasi saqlangan va yangi imkoniyatlar shu loyiha ichiga qo'shilgan.

## Imkoniyatlar

- Bosh sahifa statistikasi; shifokor, mutaxassislik, xizmat, ish jadvali va qabul boshqaruvi.
- Bemorlar ro'yxati, qidiruv, qabul holatlari va takroriy vaqtni tekshirish.
- Bemor uchun ro'yxatdan o'tish va shaxsiy kabinet: o'z qabullari, tibbiy tarixi, tahlillari, retseptlari va to'lov so'rovlari.
- Shifokor kabineti: o'z qabullari, bemorlar ro'yxati va qidiruvi, har bir bemorning qabullari, tibbiy qaydlari, tahlillari va retseptlarini ko'rish, tashxis/qayd va retsept yozish.
- Ish jadvali asosida bo'sh qabul vaqtlarini hisoblash va bronlash formasida avtomatik tanlash.
- Tibbiy tarix, laboratoriya natijalari va fayllar; tahlil fayli ruxsat tekshiruvi bilan yuklab olinadi.
- Retseptlar, to'lov yozuvlari va to'langan to'lovlar asosidagi oylik daromad hisoboti.
- Rollar: bemor, shifokor, registratura, hisobchi, laboratoriya, menejer. Rollarni `/admin/` dagi **Foydalanuvchi rollari** orqali belgilang; shifokor/bemor hisobini tegishli profilga bog'lang.
- SMS eslatma yuborish uchun Twilio integratsiyasi va yuborish jurnali.
- Gunicorn, WhiteNoise va `DATABASE_URL` bilan internetga joylashtirish uchun tayyor sozlamalar.

## Windows'da lokal ishga tushirish

Eski loyiha papkasining zaxira nusxasini oling. ZIP'ni ochib, shu papkada terminalda:

```bat
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- Sayt: http://127.0.0.1:8000/
- Admin panel: Django default admin paneli o‘chirilgan; sayt ichidagi `/admin-panel/` dan foydalaning.
- Bemor ro'yxati: http://127.0.0.1:8000/ro-yxatdan-otish/
- Kirish: http://127.0.0.1:8000/accounts/login/
- Shaxsiy kabinet: http://127.0.0.1:8000/kabinet/
- Shifokor bemorlari: http://127.0.0.1:8000/shifokor/bemorlar/ (shifokor hisobida kirganda faqat o'z bemorlari ko'rinadi)
- Hisobotlar: http://127.0.0.1:8000/hisobotlar/

Yangi ma'lumotlar bazasi migratsiyasi `0003_portal_medical_payments.py` faylida. `migrate` yangi jadvallarni yaratadi. Mavjud `db.sqlite3` faylini o'chirmang: unda avvalgi ma'lumotlaringiz bo'lishi mumkin.

## Admin'da dastlabki sozlash

1. `/admin/` ga superuser bilan kiring.
2. Mutaxassisliklar, shifokorlar, shifokor ish jadvallari va xizmatlarni kiriting.
3. Har bir shifokor uchun `User` hisobini yarating, so'ng Doctor yozuvida **Tizim foydalanuvchisi** maydoniga ulang; UserProfile rolini `doctor` qiling.
4. Shifokor kabinetida bemorlarni ko'rish uchun shifokor foydalanuvchisi `Doctor` yozuviga bog'langan bo'lishi va u bemor bilan kamida bitta qabul orqali bog'langan bo'lishi kerak. `/shifokor/bemorlar/` sahifasida faqat shu shifokorning qabullaridagi bemorlar chiqadi. Bemor kartasida qabul tarixi va klinik ma'lumotlar ko'rinadi. Bemorlar sayt orqali ro'yxatdan o'tishi mumkin. Mavjud bemorga kabinet berish uchun User yaratib, Patient yozuvidagi **Tizim foydalanuvchisi** maydoniga ulang va UserProfile rolini `patient` qiling.
5. Xodimlar uchun alohida Django foydalanuvchilari yarating. Admin panelga kira olishi kerak bo'lgan xodimlarga `is_staff` ruxsatini bering; qolganlar uchun UserProfile rolini belgilang.
6. Har bir shifokor ish jadvalini to'ldiring. Avtomatik vaqt tanlash shu jadvaldan foydalanadi.

## SMS eslatmalarni yoqish

Twilio hisobingizdan olingan ma'lumotlarni `.env.example` namunasi asosida environment variables sifatida kiriting: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`. Keyin quyidagi buyruqni qo'lda ishga tushirib ko'ring:

```bat
python manage.py send_appointment_reminders
```

Buyruq keyingi 24 soatdagi qabullar uchun SMS yuboradi. Uni har kuni yoki har soatda ishga tushirish uchun hosting cron/scheduler xizmatiga ulang. SMS uchun haqiqiy Twilio hisobi, balans va xalqaro formatdagi telefon raqamlari kerak.

## Onlayn to'lov haqida muhim eslatma

Loyihada to'lov so'rovlari, holatlari, tranzaksiya ID maydoni va daromad hisoboti mavjud. Hozircha Click/Payme'da haqiqiy pul yechish yoqilmagan: buning uchun klinikaning merchant shartnomasi/kalitlari, provayderning imzolangan callback/webhook tekshiruvi va sinovlari kerak. `To'lov so'rovi` tugmasi faqat `pending` yozuv yaratadi; u to'lovni muvaffaqiyatli deb ko'rsatmaydi. Haqiqiy integratsiyasiz bemorlardan to'lov qabul qilinmaydi.

## Internetga joylashtirish (masalan, Railway)

1. Loyihani GitHub repository'ga yuklang.
2. Hostingda yangi Django/Web service ochib, repository'ni ulang.
3. PostgreSQL xizmatini qo'shing va uning `DATABASE_URL` qiymatini web service'ga ulang.
4. Environment variables: `DJANGO_SECRET_KEY` (uzun tasodifiy qiymat), `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` va kerak bo'lsa Twilio qiymatlarini belgilang.
5. Build/deploy command sifatida `python manage.py migrate && python manage.py collectstatic --noinput` ni ishlating.
6. Start command: `gunicorn clinic_project.wsgi:application`.
7. Sayt ochilgach, hosting terminalida `python manage.py createsuperuser` bajaring va admin orqali klinika ma'lumotlarini sozlang.

## Modelni o'zgartirish

```bat
python manage.py makemigrations
python manage.py migrate
```

## Haqiqiy klinikada ishlatishdan oldin

- To'lov provayderini merchant ma'lumotlari bilan to'liq ulash va callback imzosini tekshirish.
- Zaxira nusxa, monitoring, kuchli parollar, HTTPS, maxfiy kalitlar va ma'lumotlarni saqlash siyosatini sozlash.
- Bemor ma'lumotlariga rol asosida minimal zarur ruxsat berish; qonuniy talablar bo'yicha maxfiylik tekshiruvidan o'tkazish.
- Migratsiyalar, login/rol, slot bandligi, fayl ruxsati va to'lov callback'larini staging muhitida sinash.

Bu versiyada SMS integratsiyasi Twilio hisob ma'lumotlari bilan ishlashi mumkin; haqiqiy Click/Payme tranzaksiyasi esa merchant credentials va callback integratsiyasi qo'shilmaguncha faollashtirilmagan.

## Alohida panellar
- `/admin-panel/` — sayt ichidagi administrator paneli (faqat `is_staff` yoki `is_superuser`).
- `/shifokor-paneli/` — shifokor paneli; `/kabinet/` orqali qabullarini ko'radi va bemorlar ro'yxatiga kiradi.
- `/bemor-paneli/` — bemor paneli; faqat o'z qabullari, tahlillari va retseptlarini ko'radi.
- `/admin/` — Django'ning texnik boshqaruv paneli, oddiy foydalanuvchilar uchun ruxsat berilmaydi.

Shifokor foydalanuvchisini `Doctor.user` maydoniga, bemor foydalanuvchisini `Patient.user` maydoniga bog'lang. Shifokor bemorlarni faqat o'ziga biriktirilgan qabullar orqali ko'rishi kerak.


## Sayt ichidagi panellar

- Admin paneli: `/admin-panel/` (administrator foydalanuvchisi: `is_staff` yoki `is_superuser`).
- Shifokor paneli: `/shifokor-paneli/` (foydalanuvchi Doctor yozuvining `user` maydoniga bog‘langan bo‘lishi kerak).
- Bemor paneli: `/bemor-paneli/` (foydalanuvchi Patient yozuvining `user` maydoniga bog‘langan bo‘lishi kerak).

Django standart `/admin/` paneli saytdagi menyuda ishlatilmaydi. Bosh sahifada “Barcha sozlamalar / admin” havolasi olib tashlangan.

### Shifokor paneli menyuda chiqmasa
1. Admin paneliga kiradigan administrator hisobidan foydalaning.
2. Shifokorlar bo‘limida shifokor yozuvini oching.
3. `Tizim foydalanuvchisi` (`user`) maydonida shifokorning login hisobini tanlang va saqlang.
4. Shifokor o‘z login/paroli bilan qayta kirsin.

### Bemor paneli menyuda chiqmasa
Bemorning `Tizim foydalanuvchisi` maydoniga bemor loginini bog‘lang. Ro‘yxatdan o‘tish orqali yaratilgan bemorda bu avtomatik bog‘lanadi.
