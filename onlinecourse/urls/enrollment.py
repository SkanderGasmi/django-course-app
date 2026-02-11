"""
Course enrollment URL patterns.

This module contains URL patterns for enrollment actions:
- Enroll in a course

Design decisions:
1. Action-based URLs - Use verbs for non-CRUD operations
2. Nested under course - Clear ownership hierarchy
3. POST-only - Enrollment modifies state, shouldn't be triggered by GET
4. Idempotent - Multiple enrollments handled gracefully

Security:
- CSRF protection required
- Login required (handled by view decorator)
"""
from django.urls import path
from .. import views
from .base import (
    COURSE_ID_PARAM,
    ENROLL_URL
)

# ============================================================================
# ENROLLMENT URL PATTERNS
# ============================================================================
"""
Enrollment endpoints use action-based naming:
- /<course_id>/enroll/ - Enroll in specific course
"""
urlpatterns = [
    # Course Enrollment
    # URL: /onlinecourse/<int:course_id>/enroll/
    # Methods: POST (enroll user in course)
    # View: enroll - Creates enrollment record
    # Parameter: course_id - ID of the course to enroll in
    path(
        route=f'<int:{COURSE_ID_PARAM}>/enroll/',
        view=views.enroll,
        name=ENROLL_URL
    ),
]

# ============================================================================
# URL PATTERN SUMMARY
# ============================================================================
"""
┌─────────┬───────────────────────┬──────────────────────────────┐
│ Name    │ Pattern              │ Purpose                      │
├─────────┼───────────────────────┼──────────────────────────────┤
│ enroll  │ /<course_id>/enroll/ │ Enroll user in course       │
└─────────┴───────────────────────┴──────────────────────────────┘

Example:
- POST /onlinecourse/42/enroll/ → Enroll in course 42
"""