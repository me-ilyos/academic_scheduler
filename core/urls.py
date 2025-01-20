from django.urls import path
from .views import (
    CustomLoginView,
    DepartmentAdminCreateView,
    ProfessorCreateView,
    DepartmentAdminDashboardView,
    DepartmentProfessorListView,
)
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path(
        "department/create/", DepartmentAdminCreateView.as_view(), name="admin_create"
    ),
    path("professor/create/", ProfessorCreateView.as_view(), name="professor_create"),
    path(
        "dashboard/department-admin/",
        DepartmentAdminDashboardView.as_view(),
        name="department_admin_dashboard",
    ),
    path("professors/", DepartmentProfessorListView.as_view(), name="professor_list"),
    path(
        "curriculum/create/",
        views.CurriculumFormView.as_view(),
        name="curriculum_create",
    ),
    path(
        "curriculum/<int:pk>/",
        views.CurriculumDetailView.as_view(),
        name="curriculum_detail",
    ),
    path(
        "curriculum/<int:pk>/update/",
        views.CurriculumUpdateView.as_view(),
        name="curriculum_update",
    ),
    path("curricula/", views.CurriculumListView.as_view(), name="curriculum_list"),
    path(
        "course/<int:course_id>/distribution/detail/",
        views.CourseDistributionDetailView.as_view(),
        name="course_distribution_detail",
    ),
    path(
        "course/<int:course_id>/distribute/",
        views.CourseHourDistributionView.as_view(),
        name="distribute_course_hours",
    ),
]
