"""
Exam results view for displaying submission scores and feedback.

This view is responsible for:
1. Calculating the total score for a submission
2. Providing detailed per-question feedback
3. Displaying correct answers for incorrect responses
4. Generating performance metrics and analytics

User experience goals:
- Immediate feedback - show score immediately
- Detailed breakdown - which questions were correct/incorrect
- Learning opportunity - show correct answers for mistakes
- Encouragement - positive messaging regardless of score

Performance optimization:
- All database queries are prefetched to avoid N+1
- Score calculation is O(n) where n = number of questions
- Consider caching results for large courses
"""
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Course, Submission
from .base import logger, EnrollmentRequiredMixin


@login_required
def show_exam_result(request, course_id, submission_id):
    """
    Display detailed exam results with per-question feedback.
    
    This view provides comprehensive feedback on exam performance:
    - Overall score (points earned / total points)
    - Percentage score and pass/fail status
    - For each question:
        * Whether answer was correct/incorrect
        * Points earned
        * Selected answers
        * Correct answers (for incorrect responses)
    
    Args:
        request: HTTP request object
        course_id: ID of the course
        submission_id: ID of the submission to grade
    
    Returns:
        HttpResponse: Rendered exam results template
    
    Template:
        onlinecourse/exam_result_bootstrap.html
    
    Raises:
        404: If course or submission doesn't exist
        403: If user doesn't own the submission (security check)
    """
    
    # Get course and submission objects
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    
    # SECURITY: Verify that this submission belongs to the current user
    if submission.enrollment.user != request.user:
        logger.warning(
            f"User {request.user.username} attempted to view submission #{submission_id} "
            f"belonging to user {submission.enrollment.user.username}"
        )
        messages.error(
            request,
            "You don't have permission to view this submission."
        )
        return redirect('onlinecourse:course_details', course_id=course.id)
    
    # Prefetch all necessary data to avoid N+1 queries
    # This single prefetch loads all choices and their related questions
    selected_choices = submission.choices.select_related('question').all()
    
    # Get all questions for this course (prefetched)
    questions = course.questions.prefetch_related('choices').all()
    
    # Initialize scoring accumulators
    total_score = 0
    max_score = 0
    question_results = []
    
    # Process each question
    for question in questions:
        max_score += question.grade
        
        # Get selected choices for this specific question
        selected_for_question = selected_choices.filter(question=question)
        selected_ids = list(selected_for_question.values_list('id', flat=True))
        
        # Check if answer is correct using model's business logic
        is_correct = question.is_get_score(selected_ids)
        
        if is_correct:
            total_score += question.grade
        
        # Build detailed question result for template
        question_result = {
            'question': question,
            'question_text': question.text,
            'question_grade': question.grade,
            'is_correct': is_correct,
            'earned_points': question.grade if is_correct else 0,
            'selected_ids': selected_ids,
            'selected_choices': selected_for_question,
            'correct_choices': question.choices.filter(is_correct=True),
            'all_choices': question.choices.all(),
        }
        
        question_results.append(question_result)
    
    # Calculate final score metrics
    score_percentage = (total_score / max_score * 100) if max_score > 0 else 0
    is_passing = score_percentage >= 60  # Configurable threshold
    
    # Determine performance level for messaging
    if score_percentage >= 90:
        performance_level = "excellent"
        feedback_message = "Outstanding work! You've mastered this material."
    elif score_percentage >= 75:
        performance_level = "good"
        feedback_message = "Good job! You have a solid understanding."
    elif score_percentage >= 60:
        performance_level = "passing"
        feedback_message = "You passed! Review the incorrect answers to strengthen your knowledge."
    else:
        performance_level = "needs_improvement"
        feedback_message = "Keep studying! Review the correct answers and try again."
    
    # Log submission results for analytics
    logger.info(
        f"Submission #{submission.id}: User {request.user.username}, "
        f"Course {course.name}, Score {total_score}/{max_score} "
        f"({score_percentage:.1f}%) - {'PASS' if is_passing else 'FAIL'}"
    )
    
    # Prepare template context
    context = {
        # Course information
        'course': course,
        'course_name': course.name,
        'course_id': course.id,
        
        # Submission information
        'submission': submission,
        'submission_id': submission.id,
        'submission_date': submission.created_at,
        
        # Score information
        'score': round(score_percentage, 1),
        'total_score': total_score,
        'max_score': max_score,
        'is_passing': is_passing,
        'performance_level': performance_level,
        'feedback_message': feedback_message,
        
        # Detailed results
        'question_results': question_results,
        'selected_choices': selected_choices,
        'total_questions': len(question_results),
        'correct_count': sum(1 for qr in question_results if qr['is_correct']),
        
        # Metadata for template rendering
        'show_correct_answers': True,
        'allow_retake': not is_passing,  # Allow retake only if failed
    }
    
    return render(
        request,
        'onlinecourse/exam_result_bootstrap.html',
        context
    )