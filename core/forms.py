from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import (
    UniversityUser,
    Department,
    Specialty,
    DepartmentAdminProfile,
    ProfessorProfile,
)


class DepartmentAdminForm(UserCreationForm):
    department = forms.ModelChoiceField(queryset=Department.objects.all())

    class Meta:
        model = UniversityUser
        fields = ("username", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = "DA"
        if commit:
            user.save()
            DepartmentAdminProfile.objects.create(
                user=user, department=self.cleaned_data["department"]
            )
        return user


class ProfessorForm(UserCreationForm):
    department = forms.ModelChoiceField(queryset=Department.objects.all())
    specialty = forms.ModelChoiceField(queryset=Specialty.objects.all())
    role = forms.ChoiceField(choices=ProfessorProfile.ROLE_CHOICES)

    class Meta:
        model = UniversityUser
        fields = ("username", "email", "first_name", "last_name")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = "PR"
        if commit:
            user.save()
            ProfessorProfile.objects.create(
                user=user,
                department=self.cleaned_data["department"],
                specialty=self.cleaned_data["specialty"],
                role=self.cleaned_data["role"],
            )
        return user
