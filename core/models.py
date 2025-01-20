from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.db import models


class UniversityUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ("SA", "Super Admin"),
        ("DA", "Department Admin"),
        ("PR", "Professor"),
    )

    user_type = models.CharField(max_length=2, choices=USER_TYPE_CHOICES)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    REQUIRED_FIELDS = ["email", "first_name", "last_name"]


class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    admin = models.OneToOneField(
        UniversityUser,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={"user_type": "DA"},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Specialty(models.Model):
    title = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.title


class ProfessorProfile(models.Model):
    ROLE_CHOICES = (("PR", "Professor"), ("TC", "Teacher"))
    user = models.OneToOneField(UniversityUser, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    role = models.CharField(max_length=2, choices=ROLE_CHOICES)
    specialty = models.ForeignKey(Specialty, on_delete=models.PROTECT)

    @property
    def max_hours(self):
        return 600 if self.role == "PR" else 350


class DepartmentAdminProfile(models.Model):
    user = models.OneToOneField(UniversityUser, on_delete=models.CASCADE)
    department = models.OneToOneField(Department, on_delete=models.CASCADE)


# Add to models.py
class Curriculum(models.Model):
    DEGREE_CHOICES = [("BS", "Bachelor"), ("MS", "Master of Science")]

    title = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    duration = models.IntegerField(blank=True, null=True)
    degree_type = models.CharField(max_length=2, choices=DEGREE_CHOICES)
    total_credits = models.IntegerField(blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.title}"


class Course(models.Model):
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE)
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=200)

    # Hours
    total_hours = models.IntegerField(blank=True, null=True)  # Total hours
    lecture_hours = models.IntegerField(blank=True, null=True)
    practice_hours = models.IntegerField(blank=True, null=True)
    lab_hours = models.IntegerField(blank=True, null=True)
    seminar_hours = models.IntegerField(blank=True, null=True)
    self_study_hours = models.IntegerField(blank=True, null=True)
    total_load = models.IntegerField(blank=True, null=True)  # Total load

    class Meta:
        unique_together = ["code", "curriculum"]

    def __str__(self):
        return f"{self.code} - {self.title}"


class CourseDistribution(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    # Hours per semester
    hours_sem1 = models.IntegerField(default=0)
    hours_sem2 = models.IntegerField(default=0)
    hours_sem3 = models.IntegerField(default=0)
    hours_sem4 = models.IntegerField(default=0)
    hours_sem5 = models.IntegerField(default=0)
    hours_sem6 = models.IntegerField(default=0)
    hours_sem7 = models.IntegerField(default=0)
    hours_sem8 = models.IntegerField(default=0)

    # Credits per semester
    credits_sem1 = models.IntegerField(default=0)
    credits_sem2 = models.IntegerField(default=0)
    credits_sem3 = models.IntegerField(default=0)
    credits_sem4 = models.IntegerField(default=0)
    credits_sem5 = models.IntegerField(default=0)
    credits_sem6 = models.IntegerField(default=0)
    credits_sem7 = models.IntegerField(default=0)
    credits_sem8 = models.IntegerField(default=0)
    total_credits = models.IntegerField(blank=True, null=True)

    class Meta:
        unique_together = ["course"]


@receiver(post_save, sender=UniversityUser)
def create_department_admin_profile(sender, instance, created, **kwargs):
    if created and instance.user_type == "DA":
        department = Department.objects.filter(admin=instance).first()
        if department:
            DepartmentAdminProfile.objects.create(user=instance, department=department)
