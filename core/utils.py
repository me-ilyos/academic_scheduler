# utils.py
import json
import google.generativeai as genai
from django.conf import settings


def setup_gemini():
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-pro")


def distribute_course_hours(course, selected_semesters):
    model = setup_gemini()

    prompt = f"""
    Return ONLY a raw Python dictionary with no additional formatting or text.
    
    Distribute these hours across semesters {selected_semesters}:
    lecture: {course.lecture_hours}
    practice: {course.practice_hours}
    lab: {course.lab_hours}
    seminar: {course.seminar_hours}
    self_study: {course.self_study_hours}
    
    Example output format:
    {{'sem3': {{'lecture': 24, 'practice': 12, 'lab': 12, 'seminar': 0, 'self_study': 72}}, 'sem4': {{'lecture': 24, 'practice': 12, 'lab': 12, 'seminar': 0, 'self_study': 72}}}}
    """

    try:
        response = model.generate_content(prompt)
        raw_response = response.text.strip()
        print(
            "Raw AI Response:", repr(raw_response)
        )  # Print exact response with quotes

        try:
            # Clean the response - remove any markdown code blocks if present
            cleaned_response = raw_response.replace("```python", "").replace("```", "")
            distribution = eval(cleaned_response)
            print("Parsed Distribution:", distribution)

            if validate_distribution(course, distribution, selected_semesters):
                return distribution

        except Exception as parse_error:
            print("Parsing Error:", str(parse_error))

        return fallback_distribution(course, selected_semesters)

    except Exception as e:
        print("Main Error:", str(e))
        return fallback_distribution(course, selected_semesters)


def validate_distribution(course, distribution, selected_semesters):
    hour_types = {
        "lecture": course.lecture_hours,
        "practice": course.practice_hours,
        "lab": course.lab_hours,
        "seminar": course.seminar_hours,
        "self_study": course.self_study_hours,
    }

    try:
        # Check if all selected semesters exist in distribution
        for sem in selected_semesters:
            sem_key = f"sem{sem}"
            if sem_key not in distribution:
                print(f"Missing semester {sem} in distribution")
                return False

            # Check if all hour types exist in each semester
            for hour_type in hour_types:
                if hour_type not in distribution[sem_key]:
                    print(f"Missing {hour_type} in semester {sem}")
                    return False

        # Validate total hours for each type
        for hour_type, expected_total in hour_types.items():
            actual_total = sum(
                distribution[f"sem{sem}"][hour_type] for sem in selected_semesters
            )

            if actual_total != expected_total:
                print(f"Hour mismatch for {hour_type}")
                print(f"Expected: {expected_total}")
                print(f"Got: {actual_total}")
                return False

        # Validate hour values
        for sem in selected_semesters:
            sem_key = f"sem{sem}"
            for hour_type in hour_types:
                hours = distribution[sem_key][hour_type]

                # Check if hours are integers
                if not isinstance(hours, int):
                    print(f"Non-integer hours in {sem_key} {hour_type}: {hours}")
                    return False

                # Check for negative hours
                if hours < 0:
                    print(f"Negative hours in {sem_key} {hour_type}: {hours}")
                    return False

        return True

    except Exception as e:
        print(f"Validation error: {str(e)}")
        return False


def fallback_distribution(course, selected_semesters):
    """
    Distributes hours evenly across semesters with remainder going to first semesters
    """
    distribution = {}
    num_semesters = len(selected_semesters)

    # Calculate base hours per semester
    base_hours = {
        "lecture": course.lecture_hours // num_semesters,
        "practice": course.practice_hours // num_semesters,
        "lab": course.lab_hours // num_semesters,
        "seminar": course.seminar_hours // num_semesters,
        "self_study": course.self_study_hours // num_semesters,
    }
    print(f"Base hours per semester: {base_hours}")

    # Calculate remainders
    remainders = {
        "lecture": course.lecture_hours % num_semesters,
        "practice": course.practice_hours % num_semesters,
        "lab": course.lab_hours % num_semesters,
        "seminar": course.seminar_hours % num_semesters,
        "self_study": course.self_study_hours % num_semesters,
    }
    print(f"Remainders: {remainders}")

    # First distribute base hours to each semester
    for sem in selected_semesters:
        distribution[f"sem{sem}"] = base_hours.copy()

    # Then add remainders to first semesters
    for hour_type, remainder in remainders.items():
        for i in range(remainder):
            sem = selected_semesters[i]
            distribution[f"sem{sem}"][hour_type] += 1

    print(f"Final distribution: {distribution}")
    return distribution
