"""
Views package initializer.
Exports all view classes and functions for clean imports throughout the application.
This allows us to maintain one view per file while keeping a clean API.

Import organization:
1. Base classes and mixins first
2. Authentication views
3. Course views
4. Enrollment views
5. Exam views
6. Result views

All views are exported in __all__ for wildcard imports.
"""
from .base import (
    EnrollmentCheckMixin,
    CourseContextMixin,
    logger
)
from .auth import (
    registration_request,
    login_request,
    logout_request
)
from .course import (
    CourseListView,
    CourseDetailView
)
from .enrollment import (
    enroll,
    check_if_enrolled
)
from .exam import (
    submit,
    extract_answers
)
from .results import (
    show_exam_result
)

# Export all views for easy importing
__all__ = [
    # Base
    'EnrollmentCheckMixin',
    'CourseContextMixin',
    'logger',
    
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