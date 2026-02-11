"""
Django views module - Registration file.

This file is intentionally minimal - it just imports the view functions and classes
from our well-organized package structure and exposes them at the package level.

Why this approach?
1. Separation of concerns: Each view type has its own file
2. Maintainability: Easy to locate and edit specific views
3. Testability: Can test views in isolation
4. Collaboration: Multiple developers can work on different view files
5. Performance: Only import views when needed
6. URL routing compatibility: Django's URL resolver imports from views.py

Import organization:
Views are imported in logical groups matching the URL patterns:
- Authentication views (registration, login, logout)
- Course views (list, detail)
- Enrollment views (enroll)
- Exam views (submit, extract_answers)
- Results views (show_exam_result)
"""

# ============================================================================
# IMPORT ALL VIEWS FROM MODULAR PACKAGE
# ============================================================================

# Authentication views
from .views.auth import (
    registration_request,
    login_request,
    logout_request
)

# Course views
from .views.course import (
    CourseListView,
    CourseDetailView
)

# Enrollment views
from .views.enrollment import (
    enroll,
    check_if_enrolled
)

# Exam views
from .views.exam import (
    submit,
    extract_answers
)

# Results views
from .views.results import (
    show_exam_result
)

# ============================================================================
# EXPORT ALL VIEWS
# ============================================================================
# This makes them available when importing from 'onlinecourse.views'
# and ensures Django's URL resolver can find them

__all__ = [
    # Authentication
    'registration_request',
    'login_request',
    'logout_request',
    
    # Course
    'CourseListView',
    'CourseDetailView',
    
    # Enrollment
    'enroll',
    'check_if_enrolled',
    
    # Exam
    'submit',
    'extract_answers',
    
    # Results
    'show_exam_result',
]