from academics.models import Program
from core.models import TimeStampedModel
from django.db import models
from users.models import User


# Create your models here.
class Student(TimeStampedModel):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('graduated', 'Graduated')
    ]

    student_id = models.CharField(max_length=20, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.PROTECT)
    date_of_birth = models.DateField()
    admission_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVE', 'Active'),
            ('SUSPENDED', 'Suspended'),
            ('GRADUATED', 'Graduated'),
        ]
    )

    def __str__(self):
        return f'{self.student_id}: {self.user.first_name} {self.user.last_name}'
