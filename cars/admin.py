from django.contrib import admin
from cars.models import Branch, Car, Reservation, Distance, CarBranchLog

# Register your models here.
admin.site.register(Branch)
admin.site.register(Car)
admin.site.register(Reservation)
admin.site.register(Distance)
admin.site.register(CarBranchLog)
