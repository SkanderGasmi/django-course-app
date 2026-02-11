"""
Base view classes, mixins, and utilities for the entire application.

This module provides reusable components that are shared across multiple views:
1. Mixins for common functionality (enrollment checking, course context)
2. Base view classes that can be extended
3. Shared utilities like logging configuration
4. Common context processors

Design decisions:
- Mixins are preferred over inheritance for cross-cutting concerns
- Logging is configured centrally for consistent behavior
- Helper functions are included here if used by multiple views
"""
import logging
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import ContextMixin
from ..models import Enrollment, Course

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
"""
Centralized logger configuration for all views.

Why a single logger instance?
1. Consistent log format across all views
2. Single point of configuration (log levels, handlers, formatters)
3. Easier to filter logs by application name
4. Reduces boilerplate code in each view

Usage:
    from .base import logger
    logger.info("User enrolled in course")
    logger.error("Failed to create submission", exc_info=True)
"""
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Adjust in production as needed


# ============================================================================
# MIXINS
# ============================================================================

class EnrollmentCheckMixin:
    """
    Mixin that adds enrollment checking functionality to any view.
    
    This mixin provides methods to check if the current user is enrolled
    in a specific course. It's used by both CourseListView and any
    course detail views that need to display enrollment status.
    
    Why a mixin instead of a helper function?
    - Mixins can access self.request, self.user directly
    - Can be combined with other mixins (LoginRequired, etc.)
    - Provides both method and property interfaces
    - Easier to mock in tests
    
    Usage:
        class MyView(EnrollmentCheckMixin, View):
            def get(self, request):
                if self.is_enrolled(course):
                    return self.enrolled_response()
    """
    
    def check_enrollment(self, user, course):
        """
        Check if a user is enrolled in a specific course.
        
        Args:
            user: User instance (can be AnonymousUser)
            course: Course instance to check enrollment against
        
        Returns:
            bool: True if user is authenticated AND enrolled, False otherwise
        
        Performance note:
            Uses .exists() instead of .count() > 0 which is more efficient
            as it stops at the first matching record.
        """
        if not user.is_authenticated:
            return False
        
        return Enrollment.objects.filter(
            user=user,
            course=course
        ).exists()
    
    def get_enrollment(self, user, course):
        """
        Get the enrollment object for a user and course.
        
        Args:
            user: User instance
            course: Course instance
        
        Returns:
            Enrollment: Enrollment object if exists, None otherwise
        
        Useful for views that need enrollment metadata (mode, progress, etc.)
        """
        if not user.is_authenticated:
            return None
        
        try:
            return Enrollment.objects.get(user=user, course=course)
        except Enrollment.DoesNotExist:
            return None
    
    def is_enrolled(self, course):
        """
        Property-like method that uses the current request's user.
        
        Args:
            course: Course instance to check
        
        Returns:
            bool: True if current user is enrolled
        """
        return self.check_enrollment(self.request.user, course)


class CourseContextMixin(ContextMixin):
    """
    Mixin that provides common course-related context data.
    
    This mixin standardizes the context data passed to course-related templates,
    ensuring consistency across different views (list, detail, exam, results).
    
    Common context variables:
    - course: The current course object
    - is_enrolled: Enrollment status of current user
    - enrollment: The enrollment object if enrolled
    - total_lessons: Count of lessons in the course
    - total_questions: Count of questions in the course
    
    Why a mixin?
    - Eliminates duplicate context preparation code
    - Ensures all course views have consistent template variables
    - Centralizes business logic for course metadata
    """
    
    def get_course_context(self, course):
        """
        Generate common context dictionary for course-related views.
        
        Args:
            course: Course instance
        
        Returns:
            dict: Context variables for templates
        """
        context = {
            'course': course,
            'total_lessons': course.lesson_set.count(),
            'total_questions': course.questions.count(),
            'total_points': course.total_points,
        }
        
        # Add enrollment information if user is authenticated
        if self.request.user.is_authenticated:
            enrollment = self.get_enrollment(self.request.user, course)
            context.update({
                'is_enrolled': enrollment is not None,
                'enrollment': enrollment,
            })
        
        return context


# ============================================================================
# EXCEPTIONS
# ============================================================================

class ExamSubmissionError(Exception):
    """
    Custom exception for exam submission errors.
    
    Used to differentiate exam-specific errors from general application errors.
    Allows for specific error handling in views and middleware.
    
    Example:
        try:
            submission = Submission.objects.create(...)
        except IntegrityError as e:
            raise ExamSubmissionError("Duplicate submission detected") from e
    """
    pass


class EnrollmentRequiredMixin(LoginRequiredMixin, EnrollmentCheckMixin):
    """
    Mixin that requires user to be enrolled in a course to access the view.
    
    Combines Django's LoginRequiredMixin with custom enrollment checking.
    Redirects unauthenticated users to login, and enrolled users to course detail.
    
    Usage:
        class ExamView(EnrollmentRequiredMixin, View):
            def get(self, request, course_id):
                course = get_object_or_404(Course, pk=course_id)
                # User is guaranteed to be enrolled here
    """
    
    def dispatch(self, request, *args, **kwargs):
        """Check authentication and enrollment before processing request."""
        # First check if user is authenticated
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Get course from URL kwargs
        course_id = kwargs.get('course_id')
        if not course_id:
            course_id = kwargs.get('pk')  # For DetailView
        
        if course_id:
            course = get_object_or_404(Course, pk=course_id)
            if not self.check_enrollment(request.user, course):
                # Redirect to course detail with error message
                from django.contrib import messages
                messages.error(
                    request,
                    "You must be enrolled in this course to access the exam."
                )
                return redirect('onlinecourse:course_details', course_id=course.id)
        
        return super().dispatch(request, *args, **kwargs)