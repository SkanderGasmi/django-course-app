"""
Course model representing educational courses in the platform.

The Course model is the central entity around which the entire application
revolves. It contains Lessons (content), Questions (assessments), and
Enrollments (student relationships).

Key design decisions:
1. Use CharField with max_length 30 for name - ensures UI consistency
2. Image upload path includes course ID for organization
3. Denormalized total_enrollment counter for performance
4. ManyToMany through Enrollment for additional enrollment metadata
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from .base import TimeStampedModel
from .user_profiles import Instructor


def course_image_upload_path(instance, filename):
    """
    Generate upload path for course images.
    
    Pattern: course_images/{course_id}/{filename}
    This organizes images by course and prevents filename collisions.
    
    Args:
        instance: Course instance
        filename: Original uploaded filename
    
    Returns:
        str: Path where file should be stored
    """
    # Using instance.id might be None for new courses
    # We'll use a temporary ID until the course is saved
    course_id = instance.id or 'temp'
    return f'course_images/{course_id}/{filename}'


class Course(TimeStampedModel):
    """
    Represents a complete educational course with lessons and assessments.
    
    A Course is a container for:
    - Lessons: Educational content (videos, readings, assignments)
    - Questions: Assessment items for exams
    - Instructors: Faculty teaching the course
    - Learners: Students enrolled via Enrollment model
    
    Performance considerations:
    - total_enrollment is denormalized to avoid COUNT(*) on large datasets
    - Use select_related/prefetch_related when querying related models
    """
    
    # ========================================================================
    # BASIC COURSE INFORMATION
    # ========================================================================
    name = models.CharField(
        max_length=30,
        null=False,
        default='online course',
        help_text="Short, descriptive course title (max 30 characters)."
    )
    
    description = models.CharField(
        max_length=1000,
        help_text="Detailed course description including learning objectives."
    )
    
    image = models.ImageField(
        upload_to=course_image_upload_path,
        blank=True,
        null=True,
        help_text="Course thumbnail/cover image. Recommended size: 800x600px."
    )
    
    # ========================================================================
    # PUBLICATION AND SCHEDULING
    # ========================================================================
    pub_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when course becomes publicly available."
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether course is currently active and accepting enrollments."
    )
    
    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================
    instructors = models.ManyToManyField(
        Instructor,
        related_name='courses',
        help_text="Instructors teaching this course."
    )
    
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='Enrollment',
        related_name='enrolled_courses',
        help_text="Learners enrolled in this course (via Enrollment)."
    )
    
    # ========================================================================
    # DENORMALIZED FIELDS (Performance optimization)
    # ========================================================================
    total_enrollment = models.IntegerField(
        default=0,
        help_text="Denormalized count of enrolled students. Updated via signals."
    )
    
    average_rating = models.FloatField(
        default=0.0,
        help_text="Denormalized average of enrollment ratings."
    )
    
    # ========================================================================
    # METADATA
    # ========================================================================
    class Meta:
        ordering = ['-pub_date', 'name']
        indexes = [
            models.Index(fields=['pub_date']),
            models.Index(fields=['is_active']),
        ]
    
    # ========================================================================
    # INSTANCE METHODS
    # ========================================================================
    
    def __str__(self):
        """Return course name with publication status."""
        status = "🔒" if not self.is_published else "📢"
        return f"{status} {self.name}"
    
    @property
    def is_published(self):
        """Check if course is published based on pub_date."""
        if not self.pub_date:
            return False
        return self.pub_date <= timezone.now().date()
    
    @property
    def lesson_count(self):
        """Return number of lessons in this course."""
        return self.lesson_set.count()
    
    @property
    def question_count(self):
        """Return number of questions in this course."""
        return self.questions.count()
    
    @property
    def total_points(self):
        """Sum of all question grades (total possible score)."""
        return self.questions.aggregate(
            total=models.Sum('grade')
        )['total'] or 0
    
    def update_enrollment_count(self):
        """
        Update the denormalized total_enrollment field.
        
        Called via signal when enrollments are created/deleted.
        """
        self.total_enrollment = self.enrollment_set.count()
        self.save(update_fields=['total_enrollment'])
    
    def update_average_rating(self):
        """
        Recalculate average rating from all enrollments.
        
        Called via signal when ratings are added/changed.
        """
        avg = self.enrollment_set.exclude(
            rating__isnull=True
        ).aggregate(avg=models.Avg('rating'))['avg'] or 0.0
        
        self.average_rating = round(avg, 2)
        self.save(update_fields=['average_rating'])
    
    def get_absolute_url(self):
        """Return URL for course detail view."""
        from django.urls import reverse
        return reverse('onlinecourse:course_detail', args=[self.pk])