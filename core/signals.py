from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UniversityUser, Department, DepartmentAdminProfile


@receiver(post_save, sender=UniversityUser)
def create_department_admin_profile(sender, instance, created, **kwargs):
    if created and instance.user_type == "DA":
        department = Department.objects.filter(admin=instance).first()
        if department:
            DepartmentAdminProfile.objects.create(user=instance, department=department)
