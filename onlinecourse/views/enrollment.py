"""
Enrollment views for course registration.

This module handles the enrollment workflow:
1. Checking enrollment status
2. Creating new enrollments
3. Updating course enrollment counters

Business rules:
- Users must be authenticated to enroll
- Users cannot enroll in the same course twice
- Enrollment creates a permanent record
- Course total_enrollment is denormalized for performance

Transaction management:
- Enrollment creation and course counter update are atomic
- If either operation fails, neither is committed
"""
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from ..models import Course, Enrollment
from .base import logger


def check_if_enrolled(user, course):
    """
    Check if a user is enrolled in a specific course.
    
    This is a standalone utility function used by multiple views.
    Unlike the mixin version, this can be used in function-based views
    and doesn't require access to the request object.
    
    Args:
        user: User instance (can be AnonymousUser)
        course: Course instance
    
    Returns:
        bool: True if user is authenticated and enrolled
    
    Performance note:
        Uses .exists() for early exit optimization - stops at first match
        rather than counting all matches.
    """
    if not user.is_authenticated:
        return False
    
    return Enrollment.objects.filter(
        user=user,
        course=course
    ).exists()


@login_required
@transaction.atomic
def enroll(request, course_id):
    """
    Enroll the current user in a course.
    
    This view handles the enrollment process:
    1. Verify user is authenticated (decorator)
    2. Check if already enrolled
    3. Create enrollment record
    4. Update course's denormalized enrollment counter
    5. Redirect to course detail with success message
    
    Why use @transaction.atomic?
        Both enrollment creation and course counter update must succeed
        or fail together. Without atomic transaction, we could end up with
        an enrollment but wrong counter, or counter incremented without enrollment.
    
    Args:
        request: HTTP request object
        course_id: ID of the course to enroll in
    
    Returns:
        HttpResponseRedirect: Redirect to course detail page
    
    Raises:
        404: If course doesn't exist
    """
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    
    # Check if already enrolled
    if check_if_enrolled(user, course):
        logger.info(f"User {user.username} attempted to re-enroll in course {course.id}")
        messages.info(
            request,
            f"You are already enrolled in {course.name}."
        )
        return HttpResponseRedirect(
            reverse('onlinecourse:course_details', args=[course.id])
        )
    
    # Create enrollment
    try:
        enrollment = Enrollment.objects.create(
            user=user,
            course=course,
            mode='honor',  # Default enrollment mode
            is_active=True
        )
        
        # Update denormalized enrollment counter
        course.total_enrollment += 1
        course.save(update_fields=['total_enrollment'])
        
        logger.info(
            f"User {user.username} successfully enrolled in course {course.id}"
        )
        
        messages.success(
            request,
            f"Successfully enrolled in {course.name}! You can now access the exam."
        )
        
    except Exception as e:
        logger.error(
            f"Failed to enroll user {user.username} in course {course.id}: {str(e)}",
            exc_info=True
        )
        messages.error(
            request,
            "An error occurred during enrollment. Please try again."
        )
        # Transaction will be rolled back automatically
    
    return HttpResponseRedirect(
        reverse('onlinecourse:course_details', args=[course.id])
    )