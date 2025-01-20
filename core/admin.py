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
        (
            "hours_lecture_sem1",
            "hours_practice_sem1",
            "hours_lab_sem1",
            "hours_seminar_sem1",
            "hours_self_study_sem1",
            "credits_sem1",
        ),
        (
            "hours_lecture_sem2",
            "hours_practice_sem2",
            "hours_lab_sem2",
            "hours_seminar_sem2",
            "hours_self_study_sem2",
            "credits_sem2",
        ),
        (
            "hours_lecture_sem3",
            "hours_practice_sem3",
            "hours_lab_sem3",
            "hours_seminar_sem3",
            "hours_self_study_sem3",
            "credits_sem3",
        ),
        (
            "hours_lecture_sem4",
            "hours_practice_sem4",
            "hours_lab_sem4",
            "hours_seminar_sem4",
            "hours_self_study_sem4",
            "credits_sem4",
        ),
        (
            "hours_lecture_sem5",
            "hours_practice_sem5",
            "hours_lab_sem5",
            "hours_seminar_sem5",
            "hours_self_study_sem5",
            "credits_sem5",
        ),
        (
            "hours_lecture_sem6",
            "hours_practice_sem6",
            "hours_lab_sem6",
            "hours_seminar_sem6",
            "hours_self_study_sem6",
            "credits_sem6",
        ),
        (
            "hours_lecture_sem7",
            "hours_practice_sem7",
            "hours_lab_sem7",
            "hours_seminar_sem7",
            "hours_self_study_sem7",
            "credits_sem7",
        ),
        (
            "hours_lecture_sem8",
            "hours_practice_sem8",
            "hours_lab_sem8",
            "hours_seminar_sem8",
            "hours_self_study_sem8",
            "credits_sem8",
        ),
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
