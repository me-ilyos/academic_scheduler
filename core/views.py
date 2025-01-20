from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import (
    UserPassesTestMixin,
    LoginRequiredMixin,
    UserPassesTestMixin,
    LoginRequiredMixin,
)
from django.views.generic import (
    CreateView,
    UpdateView,
    ListView,
    DetailView,
    TemplateView,
    View,
)
from django.shortcuts import render, redirect, get_object_or_404
from .forms import DepartmentAdminForm, ProfessorForm
from .models import ProfessorProfile, Curriculum, Course, CourseDistribution
from django.urls import reverse_lazy
from django.db import transaction, IntegrityError
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from .utils import distribute_course_hours


class DepartmentAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.user_type == "DA"

    def get_department(self):
        return self.request.user.departmentadminprofile.department


class CustomLoginView(LoginView):
    template_name = "core/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if user.user_type == "DA":
            return reverse_lazy("department_admin_dashboard")
        elif user.user_type == "PR":
            return reverse_lazy("professor_dashboard")
        return reverse_lazy("admin:index")


class DepartmentAdminDashboardView(
    LoginRequiredMixin, UserPassesTestMixin, TemplateView
):
    template_name = "core/department_admin_dashboard.html"

    def test_func(self):
        return self.request.user.user_type == "DA"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        department = self.request.user.departmentadminprofile.department
        context["department"] = department
        context["professors"] = department.professorprofile_set.all().select_related(
            "user", "specialty"
        )
        context["curricula"] = Curriculum.objects.filter(department=department)
        context["form"] = ProfessorForm(initial={"department": department})
        return context

    def post(self, request, *args, **kwargs):
        form = ProfessorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Professor/Teacher created successfully")
            return redirect("department_admin_dashboard")

        context = self.get_context_data()
        context["form"] = form
        return render(request, self.template_name, context)


class SuperAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class DepartmentAdminCreateView(SuperAdminRequiredMixin, CreateView):
    form_class = DepartmentAdminForm
    template_name = "core/admin_create.html"
    success_url = "/admins/"

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        department = form.cleaned_data["department"]
        department.admin = self.object
        department.save()
        return response


class ProfessorCreateView(CreateView):
    form_class = ProfessorForm
    template_name = "core/professor_create.html"
    success_url = reverse_lazy("department_admin_dashboard")

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.user_type == "DA"


class DepartmentProfessorListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = ProfessorProfile
    template_name = "core/professor_list.html"
    context_object_name = "professors"

    def test_func(self):
        return self.request.user.user_type in ["DA", "SA"]

    def get_queryset(self):
        if self.request.user.user_type == "DA":
            return ProfessorProfile.objects.filter(
                department=self.request.user.departmentadminprofile.department
            ).select_related("user", "specialty", "department")
        return ProfessorProfile.objects.all().select_related(
            "user", "specialty", "department"
        )


# Add to views.py
class CurriculumFormView(DepartmentAdminRequiredMixin, View):
    template_name = "core/curriculum_form.html"

    def get(self, request):
        return render(request, self.template_name)

    @transaction.atomic
    def post(self, request):
        try:
            # Basic validation
            required_fields = [
                "title",
                "code",
                "duration",
                "degree_type",
                "total_credits",
            ]
            for field in required_fields:
                if not request.POST.get(field):
                    messages.error(request, f"{field.title()} is required")
                    return render(request, self.template_name)

            # Create Curriculum
            curriculum = Curriculum.objects.create(
                title=request.POST["title"],
                code=request.POST["code"],
                duration=int(request.POST["duration"]),
                degree_type=request.POST["degree_type"],
                total_credits=int(request.POST["total_credits"]),
                department=self.get_department(),
            )

            # Process courses
            course_codes = request.POST.getlist("course_code[]")
            total_curriculum_credits = 0

            for i in range(len(course_codes)):
                if not course_codes[i]:  # Skip empty rows
                    continue

                try:
                    # Calculate total hours correctly
                    lecture_hours = int(request.POST.getlist("lecture_hours[]")[i] or 0)
                    practice_hours = int(
                        request.POST.getlist("practice_hours[]")[i] or 0
                    )
                    lab_hours = int(request.POST.getlist("lab_hours[]")[i] or 0)
                    seminar_hours = int(request.POST.getlist("seminar_hours[]")[i] or 0)
                    self_study_hours = int(
                        request.POST.getlist("self_study_hours[]")[i] or 0
                    )

                    total_hours = (
                        lecture_hours
                        + practice_hours
                        + lab_hours
                        + seminar_hours
                        + self_study_hours
                    )

                    # Create Course
                    course = Course.objects.create(
                        curriculum=curriculum,
                        code=course_codes[i],
                        title=request.POST.getlist("course_title[]")[i],
                        total_hours=total_hours,
                        lecture_hours=lecture_hours,
                        practice_hours=practice_hours,
                        lab_hours=lab_hours,
                        seminar_hours=seminar_hours,
                        self_study_hours=self_study_hours,
                        total_load=total_hours,  # This matches our calculated total
                    )

                    # Calculate semester credits
                    semester_credits = []
                    for sem in range(1, 9):
                        credits = int(
                            request.POST.getlist(f"credits_sem{sem}[]")[i] or 0
                        )
                        hours = int(request.POST.getlist(f"hours_sem{sem}[]")[i] or 0)
                        semester_credits.append(credits)

                    total_course_credits = sum(semester_credits)
                    total_curriculum_credits += total_course_credits

                    # Create CourseDistribution
                    distribution = CourseDistribution.objects.create(
                        course=course,
                        hours_sem1=int(request.POST.getlist("hours_sem1[]")[i] or 0),
                        hours_sem2=int(request.POST.getlist("hours_sem2[]")[i] or 0),
                        hours_sem3=int(request.POST.getlist("hours_sem3[]")[i] or 0),
                        hours_sem4=int(request.POST.getlist("hours_sem4[]")[i] or 0),
                        hours_sem5=int(request.POST.getlist("hours_sem5[]")[i] or 0),
                        hours_sem6=int(request.POST.getlist("hours_sem6[]")[i] or 0),
                        hours_sem7=int(request.POST.getlist("hours_sem7[]")[i] or 0),
                        hours_sem8=int(request.POST.getlist("hours_sem8[]")[i] or 0),
                        credits_sem1=int(
                            request.POST.getlist("credits_sem1[]")[i] or 0
                        ),
                        credits_sem2=int(
                            request.POST.getlist("credits_sem2[]")[i] or 0
                        ),
                        credits_sem3=int(
                            request.POST.getlist("credits_sem3[]")[i] or 0
                        ),
                        credits_sem4=int(
                            request.POST.getlist("credits_sem4[]")[i] or 0
                        ),
                        credits_sem5=int(
                            request.POST.getlist("credits_sem5[]")[i] or 0
                        ),
                        credits_sem6=int(
                            request.POST.getlist("credits_sem6[]")[i] or 0
                        ),
                        credits_sem7=int(
                            request.POST.getlist("credits_sem7[]")[i] or 0
                        ),
                        credits_sem8=int(
                            request.POST.getlist("credits_sem8[]")[i] or 0
                        ),
                        total_credits=total_course_credits,
                    )

                except (ValueError, IndexError) as e:
                    raise ValidationError(
                        f"Invalid data in course row {i + 1}: {str(e)}"
                    )

            # Validate total credits
            if total_curriculum_credits != int(request.POST["total_credits"]):
                raise ValidationError(
                    f"Sum of course credits ({total_curriculum_credits}) "
                    f"does not match curriculum total credits ({request.POST['total_credits']})"
                )

            messages.success(request, "Curriculum created successfully!")
            return redirect("department_admin_dashboard")

        except ValidationError as e:
            messages.error(request, str(e))
            return render(request, self.template_name)
        except IntegrityError as e:
            messages.error(request, "A curriculum with this code already exists")
            return render(request, self.template_name)
        except Exception as e:
            messages.error(request, f"Error creating curriculum: {str(e)}")
            return render(request, self.template_name)


class CurriculumDetailView(DepartmentAdminRequiredMixin, DetailView):
    model = Curriculum
    template_name = "core/curriculum_detail.html"
    context_object_name = "curriculum"

    def get_queryset(self):
        return Curriculum.objects.filter(department=self.get_department())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["courses"] = self.object.course_set.all().prefetch_related(
            "coursedistribution_set"
        )
        return context


class CurriculumUpdateView(DepartmentAdminRequiredMixin, UpdateView):
    model = Curriculum
    template_name = "core/curriculum_form.html"
    fields = ["title", "code", "duration", "degree_type", "total_credits"]

    def get_queryset(self):
        return Curriculum.objects.filter(department=self.get_department())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["courses"] = self.object.course_set.all().prefetch_related(
            "coursedistribution_set"
        )
        return context


class CurriculumListView(DepartmentAdminRequiredMixin, ListView):
    model = Curriculum
    template_name = "core/curriculum_list.html"
    context_object_name = "curricula"

    def get_queryset(self):
        return Curriculum.objects.filter(department=self.get_department())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for curriculum in context["curricula"]:
            curriculum.total_courses = curriculum.course_set.count()
        return context


# views.py
class CourseDistributionDetailView(DepartmentAdminRequiredMixin, View):
    template_name = "core/course_distribution_detail.html"

    def get(self, request, course_id):
        course = get_object_or_404(
            Course, id=course_id, curriculum__department=self.get_department()
        )
        distribution = CourseDistribution.objects.filter(course=course).first()

        # Get number of semesters from curriculum duration
        total_semesters = course.curriculum.duration * 2  # 2 semesters per year

        # Calculate lessons (2 hours per lesson)
        lecture_lessons = course.lecture_hours // 2
        practice_lessons = course.practice_hours // 2
        lab_lessons = course.lab_hours // 2
        seminar_lessons = course.seminar_hours // 2

        # Initialize semester data for all possible semesters
        semester_data = []
        for sem in range(1, total_semesters + 1):
            semester_data.append(
                {
                    "semester": sem,
                    "lecture": getattr(distribution, f"hours_sem{sem}", 0),
                    "practice": getattr(distribution, f"hours_sem{sem}", 0),
                    "lab": getattr(distribution, f"hours_sem{sem}", 0),
                    "seminar": getattr(distribution, f"hours_sem{sem}", 0),
                    "self_study": getattr(distribution, f"hours_sem{sem}", 0),
                    "total_hours": getattr(distribution, f"hours_sem{sem}", 0),
                    "credits": getattr(distribution, f"credits_sem{sem}", 0),
                }
            )

        context = {
            "course": course,
            "distribution": distribution,
            "semester_data": semester_data,
            "total_credits": distribution.total_credits if distribution else 0,
        }

        return render(request, self.template_name, context)


class CourseHourDistributionView(DepartmentAdminRequiredMixin, View):
    def post(self, request, course_id):
        try:
            course = get_object_or_404(
                Course, id=course_id, curriculum__department=self.get_department()
            )
            selected_semesters = request.POST.getlist("semesters[]")

            if not selected_semesters:
                return JsonResponse({"error": "No semesters selected"}, status=400)

            distribution = distribute_course_hours(course, selected_semesters)

            # Update CourseDistribution
            distribution_obj = CourseDistribution.objects.get_or_create(course=course)[
                0
            ]

            # Reset all semester hours
            for i in range(1, 9):
                setattr(distribution_obj, f"hours_sem{i}", 0)
                setattr(distribution_obj, f"credits_sem{i}", 0)

            # Set hours and calculate credits for selected semesters
            for sem in selected_semesters:
                sem_dist = distribution[f"sem{sem}"]
                total_sem_hours = sum(sem_dist.values())
                credits = max(
                    1, round(total_sem_hours / 30)
                )  # 1 credit = 30 hours, minimum 1 credit

                setattr(distribution_obj, f"hours_sem{sem}", total_sem_hours)
                setattr(distribution_obj, f"credits_sem{sem}", credits)

            distribution_obj.total_credits = sum(
                getattr(distribution_obj, f"credits_sem{i}", 0) for i in range(1, 9)
            )
            distribution_obj.save()

            return JsonResponse({"success": True, "distribution": distribution})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
