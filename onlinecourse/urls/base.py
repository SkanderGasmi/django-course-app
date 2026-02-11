"""
Base URL configuration, constants, and utility functions.

This module provides:
1. Shared URL constants (regex patterns, parameter names)
2. Common URL path prefixes
3. Utility functions for generating URLs
4. Centralized route naming conventions

Why centralize these?
1. DRY - Define once, use everywhere
2. Consistency - Same parameter names across all URLs
3. Maintainability - Change URL structure in one place
4. Documentation - Clear overview of URL patterns
"""
from django.urls import path, reverse
from django.utils.http import urlencode

# ============================================================================
# URL PARAMETER CONSTANTS
# ============================================================================
"""
Standardized parameter names for URL patterns.
Using constants prevents typos and ensures consistency across the codebase.
"""
PK_PARAM = 'pk'                 # Primary key parameter (for DetailView)
COURSE_ID_PARAM = 'course_id'  # Course ID parameter
SUBMISSION_ID_PARAM = 'submission_id'  # Submission ID parameter
QUESTION_ID_PARAM = 'question_id'      # Question ID parameter
CHOICE_ID_PARAM = 'choice_id'          # Choice ID parameter
USER_ID_PARAM = 'user_id'             # User ID parameter

# ============================================================================
# URL PATH PREFIXES
# ============================================================================
"""
Standardized URL path prefixes for different resource types.
These create a consistent, RESTful URL structure.
"""
COURSE_PREFIX = ''                    # Base path for courses
ENROLLMENT_PREFIX = '<int:course_id>/enroll'  # Enrollment actions
EXAM_PREFIX = '<int:course_id>/submit'        # Exam submission
RESULT_PREFIX = 'course/<int:course_id>/submission/<int:submission_id>/result'  # Results

# ============================================================================
# URL NAMING CONSTANTS
# ============================================================================
"""
Standardized URL names for reverse URL lookups.
Using constants prevents hardcoding URL names in templates and views.
"""
# Course URLs
INDEX_URL = 'index'
COURSE_DETAIL_URL = 'course_details'

# Authentication URLs
REGISTRATION_URL = 'registration'
LOGIN_URL = 'login'
LOGOUT_URL = 'logout'

# Enrollment URLs
ENROLL_URL = 'enroll'

# Exam URLs
SUBMIT_EXAM_URL = 'submit'

# Results URLs
EXAM_RESULT_URL = 'show_exam_result'


# ============================================================================
# URL UTILITY FUNCTIONS
# ============================================================================

def get_course_detail_url(course_id):
    """
    Generate URL for course detail page.
    
    Args:
        course_id: ID of the course
    
    Returns:
        str: URL path for course detail
    
    Example:
        >>> get_course_detail_url(5)
        '/onlinecourse/5/'
    """
    return reverse(f'onlinecourse:{COURSE_DETAIL_URL}', args=[course_id])


def get_enroll_url(course_id):
    """
    Generate URL for course enrollment.
    
    Args:
        course_id: ID of the course to enroll in
    
    Returns:
        str: URL path for enrollment action
    """
    return reverse(f'onlinecourse:{ENROLL_URL}', args=[course_id])


def get_submit_exam_url(course_id):
    """
    Generate URL for exam submission.
    
    Args:
        course_id: ID of the course
    
    Returns:
        str: URL path for exam submission
    """
    return reverse(f'onlinecourse:{SUBMIT_EXAM_URL}', args=[course_id])


def get_exam_result_url(course_id, submission_id):
    """
    Generate URL for exam results page.
    
    Args:
        course_id: ID of the course
        submission_id: ID of the submission
    
    Returns:
        str: URL path for exam results
    
    Example:
        >>> get_exam_result_url(5, 12)
        '/onlinecourse/course/5/submission/12/result/'
    """
    return reverse(
        f'onlinecourse:{EXAM_RESULT_URL}',
        args=[course_id, submission_id]
    )


def get_url_with_query_params(base_url, **params):
    """
    Append query parameters to a URL.
    
    Args:
        base_url: Base URL path
        **params: Query parameters as key-value pairs
    
    Returns:
        str: URL with encoded query parameters
    
    Example:
        >>> get_url_with_query_params('/search/', q='django', page=2)
        '/search/?q=django&page=2'
    """
    if params:
        return f"{base_url}?{urlencode(params)}"
    return base_url