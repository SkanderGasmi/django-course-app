"""
Admin package initialization.
Exports all admin classes for clean imports in admin.py.
This allows us to maintain one class per file while keeping a clean API.
"""
from .course import CourseAdmin
from .lesson import LessonAdmin
from .question import QuestionAdmin
from .enrollment import EnrollmentAdmin
from .submission import SubmissionAdmin
from .learner import LearnerAdmin
from .instructor import InstructorAdmin

# Export all admin classes for easy registration
__all__ = [
    'CourseAdmin',
    'LessonAdmin', 
    'QuestionAdmin',
    'EnrollmentAdmin',
    'SubmissionAdmin',
    'LearnerAdmin',
    'InstructorAdmin',
]