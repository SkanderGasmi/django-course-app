"""
Exam submission URL patterns.

This module contains URL patterns for exam-related actions:
- Submit exam answers

Why separate exam URLs?
1. Assessment is a core feature with its own logic
2. Clear separation from content viewing (courses/lessons)
3. Future extensibility (add practice exams, quizzes, etc.)
4. Security isolation - Exam endpoints need additional checks

Security considerations:
- CSRF protection required
- Login required
- Enrollment verification
- Rate limiting (future)
- Anti-cheating measures (future)
"""
from django.urls import path
from .. import views
from .base import (
    COURSE_ID_PARAM,
    SUBMIT_EXAM_URL
)

# ============================================================================
# EXAM URL PATTERNS
# ============================================================================
"""
Exam endpoints follow action-based naming:
- /<course_id>/submit/ - Submit exam for specific course
"""
urlpatterns = [
    # Exam Submission
    # URL: /onlinecourse/<int:course_id>/submit/
    # Methods: POST (submit exam answers)
    # View: submit - Creates submission with selected choices
    # Parameter: course_id - ID of the course being examined
    path(
        route=f'<int:{COURSE_ID_PARAM}>/submit/',
        view=views.submit,
        name=SUBMIT_EXAM_URL
    ),
]

# ============================================================================
# URL PATTERN SUMMARY
# ============================================================================
"""
┌────────┬─────────────────────┬──────────────────────────────┐
│ Name   │ Pattern            │ Purpose                      │
├────────┼─────────────────────┼──────────────────────────────┤
│ submit │ /<course_id>/submit/│ Submit exam answers        │
└────────┴─────────────────────┴──────────────────────────────┘

Example:
- POST /onlinecourse/42/submit/ → Submit exam for course 42
"""