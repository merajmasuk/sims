from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # Core — departments, programs, academic terms (read-only stubs)
    path("api/core/", include("apps.core.urls")),

    # Users — profiles, roles (added when module is built)
    # path("api/users/", include("apps.users.urls")),

    # Admissions
    # path("api/admissions/", include("apps.admissions.urls")),

    # Students
    # path("api/students/", include("apps.students.urls")),

    # Faculty
    # path("api/faculty/", include("apps.faculty.urls")),

    # Academics — courses, offerings
    # path("api/academics/", include("apps.academics.urls")),

    # Enrollment
    # path("api/enrollment/", include("apps.enrollment.urls")),

    # Grading
    # path("api/grading/", include("apps.grading.urls")),
]
