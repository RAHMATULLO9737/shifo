from django.urls import path, include

urlpatterns = [
    # Django default admin paneli o'chirilgan; sayt ichidagi maxsus panel ishlatiladi.
    path("", include("appointments.urls")),
]
