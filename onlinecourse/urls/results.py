"""
Exam results URL patterns.

This module contains URL patterns for viewing exam results:
- Detailed score breakdown
- Per-question feedback
- Correct answers display

URL structure philosophy:
1. Hierarchical - Results nested under submissions
2. RESTful - Resource-oriented (submission resource)
3. Read-only - Results are views, not actions
4. Permanent - Submission URLs should be bookmarkable

SEO considerations:
- Clean, readable URLs
- Include both identifiers for context
- Avoid query parameters for permanent resources
"""
from django.urls import path
from .. import views
from .base import (
    COURSE_ID_PARAM,
    SUBMISSION_ID_PARAM,
    EXAM_RESULT_URL
)

# ============================================================================
# RESULTS URL PATTERNS
# ============================================================================
"""
Results endpoints follow RESTful resource patterns:
- /course/<course_id>/submission/<submission_id>/result/
"""
urlpatterns = [
    # Exam Results
    # URL: /onlinecourse/course/<int:course_id>/submission/<int:submission_id>/result/
    # Methods: GET (view results)
    # View: show_exam_result - Displays detailed exam feedback
    # Parameters:
    #   - course_id: ID of the course
    #   - submission_id: ID of the submission to view
    path(
        route=(
            f'course/<int:{COURSE_ID_PARAM}>/'
            f'submission/<int:{SUBMISSION_ID_PARAM}>/'
            f'result/'
        ),
        view=views.show_exam_result,
        name=EXAM_RESULT_URL
    ),
]

# ============================================================================
# URL PATTERN SUMMARY
# ============================================================================
"""
┌─────────────────┬─────────────────────────────────────────────┬─────────────────┐
│ Name            │ Pattern                                    │ Purpose         │
├─────────────────┼─────────────────────────────────────────────┼─────────────────┤
│ show_exam_result│ /course/<id>/submission/<id>/result/      │ View exam scores│
└─────────────────┴─────────────────────────────────────────────┴─────────────────┘

Example:
- GET /onlinecourse/course/42/submission/123/result/
  → View results for submission 123 on course 42
"""