from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    address = models.CharField(max_length=100, blank=True, null=True)
    contact = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True, default='profile.png')
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=20, unique=True)

class Supervisor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100, blank=True, null=True)

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100, blank=True, null=True)