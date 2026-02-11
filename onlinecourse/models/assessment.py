"""
Assessment models for course exams and quizzes.

This module contains the Question and Choice models that together form
a flexible assessment system. Each question belongs to a course and
can have multiple choices, with exactly one (or more) correct answers.

Grading logic:
- Each question has a point value (grade)
- A question is considered correct if ALL correct choices are selected
  AND no incorrect choices are selected (strict scoring)
- This supports both single-answer and multiple-answer questions

Performance optimization:
- related_name='choices' for efficient prefetching
- select_related on Question when querying choices
"""
from django.db import models
from django.core.exceptions import ValidationException
from .base import TimeStampedModel


class Question(TimeStampedModel):
    """
    Represents an exam question within a course.
    
    Questions are the building blocks of course assessments. Each question
    has a text prompt, a point value, and a set of answer choices.
    
    Question types (implicitly supported):
    - Single choice: Only one correct answer
    - Multiple choice: Multiple correct answers possible
    - True/False: Two-choice variant
    - Select all that apply: Multiple correct, all must be selected
    
    Future enhancement: Add explicit question_type field for different
    scoring algorithms (partial credit, negative scoring, etc.)
    """
    
    # ========================================================================
    # CORE FIELDS
    # ========================================================================
    course = models.ForeignKey(
        'Course',
        on_delete=models.CASCADE,
        related_name='questions',
        help_text="Course this question belongs to."
    )
    
    text = models.CharField(
        max_length=500,
        help_text="The question text displayed to students."
    )
    
    # ========================================================================
    # GRADING
    # ========================================================================
    grade = models.IntegerField(
        default=1,
        help_text="Point value for this question. Must be positive."
    )
    
    # ========================================================================
    # METADATA
    # ========================================================================
    class Meta:
        ordering = ['id']
        indexes = [
            models.Index(fields=['course', 'grade']),
        ]
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def clean(self):
        """Validate question data."""
        if self.grade <= 0:
            raise ValidationException("Grade must be a positive integer.")
    
    # ========================================================================
    # INSTANCE METHODS
    # ========================================================================
    
    def __str__(self):
        """Return truncated question preview."""
        preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"[{self.grade}pts] {preview}"
    
    @property
    def choices_count(self):
        """Return total number of choices for this question."""
        return self.choices.count()
    
    @property
    def correct_choices_count(self):
        """Return number of correct choices for this question."""
        return self.choices.filter(is_correct=True).count()
    
    @property
    def has_correct_answer(self):
        """Check if question has at least one correct answer."""
        return self.correct_choices_count > 0
    
    def is_get_score(self, selected_ids):
        """
        Determine if the question should receive full points.
        
        Scoring algorithm (strict):
        - All correct choices must be selected
        - No incorrect choices can be selected
        - Returns True only if both conditions are met
        
        Args:
            selected_ids: List of Choice IDs selected by the learner
        
        Returns:
            bool: True if answer is completely correct, False otherwise
        
        Examples:
            - Single correct choice: Must select exactly that choice
            - Multiple correct: Must select ALL correct, no extras
            - No correct: Always returns False (invalid question)
        """
        # Get all correct choices for this question
        correct_choices = self.choices.filter(is_correct=True)
        correct_ids = set(correct_choices.values_list('id', flat=True))
        selected_set = set(selected_ids)
        
        # Check if all correct choices are selected AND no incorrect are selected
        return correct_ids.issubset(selected_set) and not bool(selected_set - correct_ids)
    
    def get_correct_choices_display(self):
        """
        Return formatted string of correct choices.
        
        Useful in admin interface and debugging.
        """
        correct = self.choices.filter(is_correct=True)
        if not correct.exists():
            return "⚠️ NO CORRECT ANSWER"
        
        return " | ".join([f"✓ {c.text[:30]}" for c in correct])


class Choice(TimeStampedModel):
    """
    Represents an answer choice for a question.
    
    Each choice belongs to exactly one question and has a text label
    and a boolean indicating whether it's correct.
    
    Design decision:
    We use a boolean is_correct field rather than a separate CorrectAnswer
    model. This simplifies queries and maintains data integrity with
    database constraints (at least one is_correct=True per question).
    """
    
    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices',  # Enables question.choices.all()
        help_text="Question this choice belongs to."
    )
    
    # ========================================================================
    # CHOICE CONTENT
    # ========================================================================
    text = models.CharField(
        max_length=200,
        help_text="Answer text displayed to students."
    )
    
    is_correct = models.BooleanField(
        default=False,
        help_text="Whether this is a correct answer choice."
    )
    
    # ========================================================================
    # METADATA
    # ========================================================================
    class Meta:
        ordering = ['question', 'id']
        indexes = [
            models.Index(fields=['question', 'is_correct']),
        ]
    
    # ========================================================================
    # INSTANCE METHODS
    # ========================================================================
    
    def __str__(self):
        """Return choice preview with correctness indicator."""
        indicator = "✓" if self.is_correct else "○"
        preview = self.text[:30] + "..." if len(self.text) > 30 else self.text
        return f"{indicator} {preview}"
    
    def clean(self):
        """
        Validate choice data.
        
        Ensures each question has at least one correct answer.
        This validation runs when saving individual choices.
        """
        super().clean()
        
        # Skip validation for existing records if we're just toggling is_correct
        if not self.pk and not self.is_correct:
            # New incorrect choice - no validation needed
            return
        
        # Check if this would leave the question without any correct answers
        if not self.is_correct and self.pk:
            # We're making a previously correct choice incorrect
            other_correct = self.question.choices.filter(
                is_correct=True
            ).exclude(pk=self.pk).exists()
            
            if not other_correct:
                raise ValidationException(
                    "Question must have at least one correct answer."
                )