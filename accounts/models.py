from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class User(AbstractUser):
    class Role(models.TextChoices):
        TEACHER = "TEACHER"
        REGISTRAR = "REGISTRAR"
        PRINCIPAL = "PRINCIPAL"
        ADMIN = "ADMIN"
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.TEACHER)