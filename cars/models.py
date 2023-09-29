from django.db import models
from django.core.validators import RegexValidator


class CarNumberField(models.CharField):
    default_validators = [
        RegexValidator(
            regex="^C[0-9]+$",
            message="car_number must be in the format C<number>",
            code="invalid_car_number",
        )
    ]
    description = "Car Number"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 254)
        super().__init__(*args, **kwargs)


class Branch(models.Model):
    city = models.CharField(max_length=100)


class Car(models.Model):
    id = models.BigAutoField(primary_key=True)
    car_number = CarNumberField(unique=True)
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Car, self).save(*args, **kwargs)


class Reservation(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    pickup_branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="pickup_branch"
    )
    return_branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="return_branch"
    )
