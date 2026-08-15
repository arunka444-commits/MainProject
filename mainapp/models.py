from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Profilee(models.Model):
    ROLE_CHOICES = (
        ("ADMIN", "Admin"),
        ("EMPLOYEE", "Employee"),
        ("USER", "User"),
        ("SERVICE_PROVIDER", "ServiceProvider"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, blank=True, null=True)
    skill = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.user.username




class addservice(models.Model):
    service_provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    service_name = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    STATUS_CHOICES = (
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.service_name


class Booking(models.Model):
    STATUS_CHOICES = (
        ("Pending", "Pending"),
        ("Accepted", "Accepted"),
        ("Rejected", "Rejected"),
        ("Completed", "Completed"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_bookings"
    )

    service_provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="provider_bookings"
    )

    service_name = models.CharField(max_length=200)

    assigned_employee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_bookings"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.service_name}"


#for total bookibg,user,serviceprovider display in admin page 
   


class ServiceProvider(models.Model):
        user = models.OneToOneField(User, on_delete=models.CASCADE)
        company_name = models.CharField(max_length=200)



        def __str__(self):
            return self.company_name



class CustomerBooking(models.Model):


    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    service_name = models.CharField(max_length=200)
    booking_date = models.DateField(auto_now_add=True)
    

    def __str__(self):
        return self.service_name
