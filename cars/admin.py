from django.contrib import admin
from cars.models import Branch, Car, Reservation

# Register your models here.
admin.site.register(Branch)
admin.site.register(Car)
admin.site.register(Reservation)