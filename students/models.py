from django.contrib.auth.models import AbstractUser
from django.db import models

import uuid


# Create your models here.
class Student(AbstractUser):
	id = models.UUIDField(default=uuid.uuid4, unique=True, null=False)
	first_name = models.CharField(max_length=200, null=True, blank=True)
	last_name = models.CharField(max_length=200, null=True, blank=True)
	token = models.CharField(max_length=200, null=True, blank=True)
	email = models.EmailField(null=False, blank=False)
	phone_number = models.CharField(max_length=50, null=True, blank=True)
	date_of_birth = models.DateField()

	is_deleted = models.BooleanField(default=False)

	@property
	def full_name(self):
		return f"{self.first_name} {self.last_name}".strip()
