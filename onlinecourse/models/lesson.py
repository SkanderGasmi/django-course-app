"""
Lesson model representing individual content units within a course.

A Lesson is a self-contained educational unit that could be a video lecture,
reading assignment, quiz, or interactive exercise. Lessons are ordered within
a course to create a learning path.

Content management:
- Content can be text, HTML, or embed codes for videos
- Order field allows flexible reordering
- Each lesson belongs to exactly one course
"""
from django.db import models
from django.utils.html import strip_tags
from .base import TimeStampedModel


class Lesson(TimeStampedModel):
    """
    Represents a single lesson within a course.
    
    Lessons are the primary content delivery mechanism. They can contain:
    - Written content (text/HTML)
    - Embedded videos (YouTube, Vimeo)
    - Code examples
    - Downloadable resources
    
    Ordering strategy:
    We use an IntegerField for manual ordering rather than a FloatField
    with gaps. This makes reordering more intuitive for instructors.
    """
    
    # ========================================================================
    # LESSON CONTENT
    # ========================================================================
    title = models.CharField(
        max_length=200,
        default="Untitled Lesson",
        help_text="Descriptive title for the lesson."
    )
    
    content = models.TextField(
        help_text="Main lesson content. Can include HTML markup for formatting."
    )
    
    # ========================================================================
    # MEDIA AND RESOURCES
    # ========================================================================
    video_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="YouTube/Vimeo embed URL for video lectures."
    )
    
    duration_minutes = models.IntegerField(
        default=30,
        help_text="Estimated time to complete this lesson (in minutes)."
    )
    
    # ========================================================================
    # ORGANIZATION
    # ========================================================================
    order = models.IntegerField(
        default=0,
        help_text="Display order within course. Lower numbers appear first."
    )
    
    course = models.ForeignKey(
        'Course',
        on_delete=models.CASCADE,
        help_text="Parent course containing this lesson."
    )
    
    # ========================================================================
    # METADATA
    # ========================================================================
    class Meta:
        ordering = ['order', 'created_at']
        unique_together = ['course', 'order']  # Prevent duplicate order numbers
        indexes = [
            models.Index(fields=['course', 'order']),
        ]
    
    # ========================================================================
    # INSTANCE METHODS
    # ========================================================================
    
    def __str__(self):
        """Return lesson title with course context."""
        return f"{self.course.name} → {self.title}"
    
    @property
    def content_preview(self):
        """
        Return plain text preview of content (HTML stripped).
        
        Useful for admin list displays and search indexing.
        """
        if not self.content:
            return ""
        
        plain_text = strip_tags(self.content)
        return plain_text[:150] + "..." if len(plain_text) > 150 else plain_text
    
    @property
    def has_video(self):
        """Check if lesson includes video content."""
        return bool(self.video_url)
    
    @property
    def has_content(self):
        """Check if lesson has any content."""
        return bool(self.content or self.video_url)
    
    def get_next_lesson(self):
        """Return the next lesson in the course sequence."""
        return Lesson.objects.filter(
            course=self.course,
            order__gt=self.order
        ).order_by('order').first()
    
    def get_previous_lesson(self):
        """Return the previous lesson in the course sequence."""
        return Lesson.objects.filter(
            course=self.course,
            order__lt=self.order
        ).order_by('-order').first()