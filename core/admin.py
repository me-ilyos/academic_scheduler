from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    UniversityUser,
    Department,
    Specialty,
    ProfessorProfile,
    DepartmentAdminProfile,
    Curriculum,
    Course,
    CourseDistribution,
)


@admin.register(UniversityUser)
class UniversityUserAdmin(UserAdmin):
    list_display = ("username", "email", "user_type", "is_staff")
    list_filter = ("user_type", "is_staff")
    fieldsets = UserAdmin.fieldsets + (("User Type", {"fields": ("user_type",)}),)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "admin")
    search_fields = ("code", "name")


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ("code", "title")
    search_fields = ("code", "title")


@admin.register(ProfessorProfile)
class ProfessorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "role", "specialty", "max_hours")
    list_filter = ("role", "department")
    search_fields = ("user__username", "specialty__title")


@admin.register(DepartmentAdminProfile)
class DepartmentAdminProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "department")
    search_fields = ("user__username", "department__name")


# Add to admin.py


class CourseDistributionInline(admin.TabularInline):
    model = CourseDistribution
    extra = 0
    can_delete = True
    fields = [
        ("hours_sem1", "credits_sem1"),
        ("hours_sem2", "credits_sem2"),
        ("hours_sem3", "credits_sem3"),
        ("hours_sem4", "credits_sem4"),
        ("hours_sem5", "credits_sem5"),
        ("hours_sem6", "credits_sem6"),
        ("hours_sem7", "credits_sem7"),
        ("hours_sem8", "credits_sem8"),
        "total_credits",
    ]


class CourseInline(admin.TabularInline):
    model = Course
    extra = 0
    can_delete = True
    show_change_link = True
    fields = [
        "code",
        "title",
        "total_hours",
        "lecture_hours",
        "practice_hours",
        "lab_hours",
        "seminar_hours",
        "self_study_hours",
        "total_load",
    ]


@admin.register(Curriculum)
class CurriculumAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "title",
        "department",
        "degree_type",
        "duration",
        "total_credits",
        "created_at",
    ]
    list_filter = ["department", "degree_type", "duration"]
    search_fields = ["code", "title"]
    inlines = [CourseInline]
    ordering = ["-created_at"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "title",
        "curriculum",
        "total_hours",
        "lecture_hours",
        "practice_hours",
        "lab_hours",
    ]
    list_filter = ["curriculum__department", "curriculum"]
    search_fields = ["code", "title"]
    inlines = [CourseDistributionInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("curriculum")
