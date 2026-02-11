"""
Django models module

This file is intentionally minimal - it just imports the model classes
from our well-organized package structure and exposes them at the package level.

Why this approach?
1. Separation of concerns: Each model class has its own file
2. Maintainability: Easy to locate and edit specific models
3. Testability: Can test models in isolation
4. Collaboration: Multiple developers can work on different model files
5. Performance: Only load what's needed
6. Migration compatibility: Django's makemigrations works through this file

Import order:
Models are imported in dependency order (base models first, then models that
depend on them, etc.) to ensure all references are resolvable.
"""

# ============================================================================
# BASE MODELS (Abstract classes, no database tables)
# ============================================================================
from .models.base import TimeStampedModel, AbstractUserProfile


# ============================================================================
# USER PROFILE MODELS (Extend Django User)
# ============================================================================
from .models.user_profiles import Instructor, Learner

# ============================================================================
# CORE COURSE MODELS (Course structure hierarchy)
# ============================================================================
from .models.course import Course
from .models.lesson import Lesson

# ============================================================================
# ENROLLMENT MODEL (Links users to courses)
# ============================================================================
from .models.enrollment import Enrollment

# ============================================================================
# ASSESSMENT MODELS (Questions and choices)
# ============================================================================
from .models.assessment import Question, Choice

# ============================================================================
# SUBMISSION MODEL (Exam attempts)
# ============================================================================
from .models.submission import Submission

# ============================================================================
# EXPORT ALL MODELS
# ============================================================================
# This makes them available when importing from 'onlinecourse.models'
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