"""
Models package initializer.
Exports all model classes for clean imports throughout the application.
This allows us to maintain one class per file while keeping a clean API.

Import organization:
1. Base models and mixins first
2. Dependent models in order of dependency
3. All models exported in __all__ for wildcard imports
"""
from .base import TimeStampedModel, AbstractUserProfile
from .user_profiles import Instructor, Learner
from .course import Course
from .lesson import Lesson
from .enrollment import Enrollment
from .assessment import Question, Choice
from .submission import Submission

# Export all models for easy importing
__all__ = [
    # Base
    'TimeStampedModel',
    'AbstractUserProfile',
    
    # User Profiles
    'Instructor',
    'Learner',
    
    # Course Structure
    'Course',
    'Lesson',
    
    # Enrollment
    'Enrollment',
    
    # Assessment
    'Question',
    'Choice',
    
    # Submission
    'Submission',
]