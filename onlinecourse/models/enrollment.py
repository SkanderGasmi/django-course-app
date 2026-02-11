"""
Enrollment model linking users to courses with additional metadata

The Enrollment model serves as a through model for the ManyToMany relationship
between User and Course. This allows us to track enrollment-specific data:
- When the user enrolled
- Enrollment mode (audit, honor, beta)
- User's rating of the course
- Progress tracking
- Final grade

This is a classic example of the "Association Class" pattern in UML.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from .base import TimeStampedModel


class Enrollment(TimeStampedModel):
    """
    Represents a student's enrollment in a specific course.
    
    This model captures the many-to-many relationship between User and Course
    with additional attributes specific to each enrollment instance.
    
    Design rationale:
    We use explicit through model rather than automatic ManyToMany field
    because we need to store enrollment-specific data (mode, date, rating).
    
    Business rules:
    - Users can only have one active enrollment per course
    - Audit mode: Free access, no certificate
    - Honor mode: Verified, certificate eligible
    - Beta mode: Early access, provide feedback
    """
    
    # ========================================================================
    # ENROLLMENT MODES
    # ========================================================================
    AUDIT = 'audit'
    HONOR = 'honor'
    BETA = 'beta'
    VERIFIED = 'verified'
    
    COURSE_MODES = [
        (AUDIT, 'Audit - Free access, no certificate'),
        (HONOR, 'Honor - Free with honor code, certificate eligible'),
        (BETA, 'Beta - Early access, provide feedback'),
        (VERIFIED, 'Verified - Paid, verified certificate'),
    ]
    
    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="Student enrolling in the course."
    )
    
    course = models.ForeignKey(
        'Course',
        on_delete=models.CASCADE,
        help_text="Course being enrolled in."
    )
    
    # ========================================================================
    # ENROLLMENT DETAILS
    # ========================================================================
    date_enrolled = models.DateField(
        default=timezone.now,
        help_text="Date when enrollment was created."
    )
    
    mode = models.CharField(
        max_length=10,
        choices=COURSE_MODES,
        default=AUDIT,
        help_text="Enrollment type determining access level and certification."
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether enrollment is currently active."
    )
    
    # ========================================================================
    # PROGRESS AND GRADES
    # ========================================================================
    progress_percent = models.IntegerField(
        default=0,
        help_text="Percentage of course completed (0-100)."
    )
    
    final_grade = models.FloatField(
        null=True,
        blank=True,
        help_text="Final course grade percentage (0-100)."
    )
    
    completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when course was completed (if applicable)."
    )
    
    # ========================================================================
    # FEEDBACK
    # ========================================================================
    rating = models.FloatField(
        null=True,
        blank=True,
        help_text="Course rating given by student (1.0-5.0)."
    )
    
    review = models.TextField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="Written course review/feedback."
    )
    
    # ========================================================================
    # METADATA
    # ========================================================================
    class Meta:
        unique_together = ['user', 'course']  # Prevent duplicate enrollments
        ordering = ['-date_enrolled']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['course', 'is_active']),
        ]
    
    # ========================================================================
    # INSTANCE METHODS
    # ========================================================================
    
    def __str__(self):
        """Return enrollment summary."""
        status = "✓" if self.completion_date else "⋯"
        return f"{status} {self.user.username} @ {self.course.name} ({self.get_mode_display()})"
    
    @property
    def is_completed(self):
        """Check if course has been completed."""
        return self.completion_date is not None
    
    def complete_course(self, grade=None):
        """
        Mark enrollment as completed with optional final grade.
        
        Args:
            grade: Final grade percentage (0-100). If None, calculates automatically.
        """
        self.completion_date = timezone.now().date()
        self.progress_percent = 100
        
        if grade is not None:
            self.final_grade = grade
        
        self.save()
    
    def update_progress(self):
        """
        Calculate and update progress percentage based on submissions.
        
        Progress is calculated as ratio of questions answered vs total questions.
        This is an approximation and could be enhanced to track lesson completion.
        """
        course = self.course
        total_questions = course.questions.count()
        
        if total_questions == 0:
            self.progress_percent = 0
        else:
            # Count distinct questions answered in submissions
            answered_questions = self.submission_set.values(
                'choices__question'
            ).distinct().count()
            
            self.progress_percent = int(
                (answered_questions / total_questions) * 100
            )
        
        self.save(update_fields=['progress_percent'])
    
    def save(self, *args, **kwargs):
        """
        Override save to update course enrollment count.
        
        For new enrollments, increment the course's total_enrollment counter.
        This is a denormalization optimization.
        """
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            self.course.total_enrollment += 1
            self.course.save(update_fields=['total_enrollment'])