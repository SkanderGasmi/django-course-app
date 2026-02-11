"""
Exam submission views for handling student exam attempts.

This module contains the core assessment logic:
1. Submit: Create submission record with selected choices
2. Extract Answers: Parse form data to extract selected choices
3. Validation: Ensure submission is valid and complete

Critical business logic:
- Each submission represents one exam attempt
- Submissions are immutable once created
- Multiple submissions per enrollment are allowed (retakes)
- All choices must belong to the course being examined

Security considerations:
- Verify user is enrolled before allowing submission
- Prevent cross-course answer injection
- Validate that selected choices belong to the course
- Rate limiting to prevent spam (future enhancement)
"""
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from ..models import Course, Enrollment, Choice, Submission
from .base import logger, ExamSubmissionError, EnrollmentRequiredMixin
import re


def extract_answers(request):
    """
    Extract selected choice IDs from the exam form submission.
    
    Form field naming convention:
        choice_<id> - Checkbox input for a specific choice
        Example: <input type="checkbox" name="choice_42" value="selected">
    
    Why this format?
    1. Easy to parse - split on underscore
    2. Self-documenting - clearly indicates a choice selection
    3. Compatible with Django's form handling
    4. Supports multiple selections for the same question
    
    Args:
        request: HTTP request object containing POST data
    
    Returns:
        list: Integer IDs of selected choices
    
    Example:
        POST data: {'choice_1': 'selected', 'choice_3': 'selected'}
        Returns: [1, 3]
    """
    selected_choices = []
    
    # Pattern to match field names like 'choice_123'
    choice_pattern = re.compile(r'^choice_(\d+)$')
    
    for field_name in request.POST.keys():
        match = choice_pattern.match(field_name)
        if match:
            choice_id = int(match.group(1))
            selected_choices.append(choice_id)
    
    logger.debug(f"Extracted {len(selected_choices)} selected choices from form")
    
    return selected_choices


@login_required
@transaction.atomic
def submit(request, course_id):
    """
    Submit exam answers and create a submission record.
    
    This is the most critical view in the assessment system. It:
    1. Validates the user is enrolled in the course
    2. Creates a submission record linked to the enrollment
    3. Associates all selected choices with the submission
    4. Redirects to the results page for immediate feedback
    
    Data integrity guarantees:
    - All operations are atomic (rollback on any failure)
    - Submission timestamp is automatically recorded
    - Each choice is validated to exist and belong to the course
    - Duplicate choices are prevented (ManyToMany handles uniqueness)
    
    Args:
        request: HTTP request object with POST data
        course_id: ID of the course being examined
    
    Returns:
        HttpResponseRedirect: Redirect to exam results page
    
    Raises:
        404: If course or enrollment doesn't exist
        403: If user is not enrolled (handled by decorator)
    
    Template:
        No direct template - redirects to show_exam_result
    """
    # Get course and verify it exists
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    
    # Get or verify enrollment exists
    try:
        enrollment = Enrollment.objects.get(user=user, course=course)
    except Enrollment.DoesNotExist:
        logger.warning(
            f"User {user.username} attempted to submit exam for course {course_id} "
            f"but is not enrolled"
        )
        messages.error(
            request,
            "You must be enrolled in this course to take the exam."
        )
        return redirect('onlinecourse:course_details', course_id=course.id)
    
    # Extract selected choices from form
    selected_choice_ids = extract_answers(request)
    
    if not selected_choice_ids:
        logger.info(
            f"User {user.username} submitted exam for course {course.id} "
            f"with no answers selected"
        )
        messages.warning(
            request,
            "You didn't select any answers. Please try again."
        )
        return redirect('onlinecourse:course_details', course_id=course.id)
    
    # Validate that all selected choices belong to this course
    valid_choices = Choice.objects.filter(
        id__in=selected_choice_ids,
        question__course=course
    )
    
    valid_choice_ids = set(valid_choices.values_list('id', flat=True))
    invalid_choice_ids = set(selected_choice_ids) - valid_choice_ids
    
    if invalid_choice_ids:
        logger.error(
            f"User {user.username} attempted to submit choices {invalid_choice_ids} "
            f"that do not belong to course {course.id}"
        )
        raise ExamSubmissionError(
            f"Invalid choice IDs detected: {invalid_choice_ids}"
        )
    
    # Create submission and add choices
    try:
        submission = Submission.objects.create(enrollment=enrollment)
        submission.choices.set(valid_choices)  # More efficient than add() per item
        
        logger.info(
            f"Submission #{submission.id} created for user {user.username} "
            f"on course {course.id} with {valid_choices.count()} choices"
        )
        
        messages.success(
            request,
            "Exam submitted successfully! Your score is shown below."
        )
        
    except Exception as e:
        logger.error(
            f"Failed to create submission for user {user.username} on course {course.id}: {str(e)}",
            exc_info=True
        )
        messages.error(
            request,
            "An error occurred while submitting your exam. Please try again."
        )
        return redirect('onlinecourse:course_details', course_id=course.id)
    
    # Redirect to results page
    return redirect(
        'onlinecourse:show_exam_result',
        course_id=course.id,
        submission_id=submission.id
    )