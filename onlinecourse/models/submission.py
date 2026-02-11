"""
Submission model representing student exam attempts.

A Submission records all choices a student makes when taking an exam.
Each submission is linked to an enrollment and has a many-to-many
relationship with selected choices.

Data integrity:
- Submissions are immutable once created (read-only in admin)
- Each enrollment can have multiple submissions (exam attempts)
- Choices are snapshotted at time of submission (not live updates)

Performance:
- Use prefetch_related('choices__question') when calculating scores
- Consider caching calculated scores for frequently accessed submissions
"""
from django.db import models
from django.utils import timezone
from .base import TimeStampedModel


class Submission(TimeStampedModel):
    """
    Represents a single exam submission by a learner.
    
    When a student completes an exam, we create a Submission record
    that captures all their selected answers. This provides:
    1. An audit trail of student work
    2. The ability to grade and re-grade submissions
    3. Analytics on question difficulty and common mistakes
    
    Design decision:
    We store only the selected choices, not the answers they replaced.
    This is sufficient for grading and analysis. If we need version history,
    we would implement a more complex system with snapshots.
    """
    
    # ========================================================================
    # CORE FIELDS
    # ========================================================================
    enrollment = models.ForeignKey(
        'Enrollment',
        on_delete=models.CASCADE,
        help_text="Enrollment context for this submission."
    )
    
    choices = models.ManyToManyField(
        'Choice',
        help_text="Selected answer choices for the exam."
    )
    
    # ========================================================================
    # TIMESTAMPS (inherited from TimeStampedModel)
    # ========================================================================
    # created_at: Auto-set to submission time
    # updated_at: Auto-updated if submission is modified
    
    # ========================================================================
    # METADATA
    # ========================================================================
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['enrollment', 'created_at']),
            models.Index(fields=['enrollment__course']),
        ]
        get_latest_by = 'created_at'
    
    # ========================================================================
    # INSTANCE METHODS
    # ========================================================================
    
    def __str__(self):
        """Return submission summary."""
        return f"Submission #{self.id}: {self.enrollment.user.username} - {self.enrollment.course.name}"
    
    @property
    def course(self):
        """Convenience property to access course via enrollment."""
        return self.enrollment.course
    
    @property
    def user(self):
        """Convenience property to access user via enrollment."""
        return self.enrollment.user
    
    @property
    def submission_date(self):
        """Alias for created_at for backward compatibility."""
        return self.created_at
    
    def get_score(self):
        """
        Calculate total score for this submission.
        
        This method iterates through all questions in the course,
        checks if the selected choices are correct using the question's
        is_get_score() method, and sums the points.
        
        Performance note:
        For bulk operations, use the cached_score field approach.
        For single submissions, this method is fine.
        
        Returns:
            tuple: (earned_points, total_possible_points)
        """
        total_score = 0
        max_score = 0
        
        for question in self.course.questions.all():
            max_score += question.grade
            
            # Get IDs of selected choices for this question
            selected_ids = self.choices.filter(
                question=question
            ).values_list('id', flat=True)
            
            if question.is_get_score(list(selected_ids)):
                total_score += question.grade
        
        return total_score, max_score
    
    def get_score_percentage(self):
        """
        Calculate score as percentage.
        
        Returns:
            float: Score percentage (0-100)
        """
        earned, total = self.get_score()
        if total == 0:
            return 0.0
        return (earned / total) * 100
    
    def is_passing(self, passing_threshold=60):
        """
        Check if submission meets passing threshold.
        
        Args:
            passing_threshold: Minimum percentage to pass (default: 60)
        
        Returns:
            bool: True if score >= threshold
        """
        return self.get_score_percentage() >= passing_threshold
    
    def get_answers_by_question(self):
        """
        Group selected choices by question.
        
        Returns:
            dict: Mapping of question_id -> list of selected Choice objects
        
        Example:
            {
                1: [<Choice: Paris>, <Choice: London>],
                2: [<Choice: True>],
            }
        """
        answers = {}
        for choice in self.choices.select_related('question').all():
            q_id = choice.question_id
            if q_id not in answers:
                answers[q_id] = []
            answers[q_id].append(choice)
        return answers
    
    def get_incorrect_questions(self):
        """
        Identify questions answered incorrectly.
        
        Returns:
            QuerySet: Question objects that were answered incorrectly
        """
        incorrect = []
        for question in self.course.questions.all():
            selected_ids = self.choices.filter(
                question=question
            ).values_list('id', flat=True)
            
            if not question.is_get_score(list(selected_ids)):
                incorrect.append(question.pk)
        
        from .assessment import Question
        return Question.objects.filter(pk__in=incorrect)