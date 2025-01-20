# utils.py
import google.generativeai as genai
from django.conf import settings


def setup_gemini():
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-pro")


# utils.py
def distribute_course_hours(course, selected_semesters):
    model = setup_gemini()

    # Calculate lessons (2 hours per lesson)
    lecture_lessons = course.lecture_hours // 2
    practice_lessons = course.practice_hours // 2
    lab_lessons = course.lab_hours // 2
    seminar_lessons = course.seminar_hours // 2

    prompt = f"""
    I need to distribute course lessons across {len(selected_semesters)} semesters: {selected_semesters}.
    Each lesson is 2 hours.
    Course has following lessons:
    - Lecture lessons: {lecture_lessons} (total {course.lecture_hours} hours)
    - Practice lessons: {practice_lessons} (total {course.practice_hours} hours)
    - Lab lessons: {lab_lessons} (total {course.lab_hours} hours)
    - Seminar lessons: {seminar_lessons} (total {course.seminar_hours} hours)
    - Self study hours: {course.self_study_hours}
    
    Rules:
    1. Return JSON with distribution for each type per semester
    2. Each lesson type should sum up to its total lessons
    3. Not all semesters need equal distribution
    4. Hours in response should be actual hours (lessons * 2)
    5. If hours for type is 0, return 0 for all semesters
    6. Each lesson is exactly 2 hours
    
    Example output format:
    {{
        "sem1": {{"lecture": 30, "practice": 20, "lab": 0, "seminar": 0, "self_study": 30}},
        "sem2": {{"lecture": 30, "practice": 20, "lab": 0, "seminar": 0, "self_study": 30}}
    }}
    """

    response = model.generate_content(prompt)
    try:
        distribution = eval(response.text)
        validate_distribution(course, distribution, selected_semesters)
        return distribution
    except:
        return fallback_distribution(course, selected_semesters)


def validate_distribution(course, distribution, semesters):
    hour_types = {
        "lecture": course.lecture_hours,
        "practice": course.practice_hours,
        "lab": course.lab_hours,
        "seminar": course.seminar_hours,
        "self_study": course.self_study_hours,
    }

    for hour_type, total in hour_types.items():
        distributed_sum = sum(distribution[f"sem{sem}"][hour_type] for sem in semesters)
        if distributed_sum != total:
            raise ValueError(f"Invalid distribution for {hour_type}")


def fallback_distribution(course, selected_semesters):
    """Fallback distribution when AI fails"""
    distribution = {}
    num_semesters = len(selected_semesters)

    for sem in selected_semesters:
        # Calculate base hours per semester
        lecture_per_sem = course.lecture_hours // num_semesters
        practice_per_sem = course.practice_hours // num_semesters
        lab_per_sem = course.lab_hours // num_semesters
        seminar_per_sem = course.seminar_hours // num_semesters
        self_study_per_sem = course.self_study_hours // num_semesters

        distribution[f"sem{sem}"] = {
            "lecture": lecture_per_sem,
            "practice": practice_per_sem,
            "lab": lab_per_sem,
            "seminar": seminar_per_sem,
            "self_study": self_study_per_sem,
        }

    # Handle remainders
    remainder = {
        "lecture": course.lecture_hours % num_semesters,
        "practice": course.practice_hours % num_semesters,
        "lab": course.lab_hours % num_semesters,
        "seminar": course.seminar_hours % num_semesters,
        "self_study": course.self_study_hours % num_semesters,
    }

    # Distribute remainders to first semesters
    for hour_type, remaining in remainder.items():
        for i in range(remaining):
            sem = selected_semesters[i]
            distribution[f"sem{sem}"][hour_type] += 1

    return distribution
