"""
Base models and mixins for the entire application

This module provides abstract base classes that are inherited by all models
throughout the application. Centralizing common functionality here ensures:
1. DRY principle - common fields and methods defined once
2. Consistency - all models share same behavior for timestamps, etc.
3. Maintainability - changes propagate to all models automatically

Design decisions:
- Use abstract base classes (no database tables created)
- Provide sensible defaults for all fields
- Include audit timestamps on all models for traceability
"""
from django.db import models
from django.utils import timezone
import uuid


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides automatic timestamp fields.
    
    Why this exists:
    Every model in our system should track when records are created and updated.
    This is crucial for:
    - Auditing: Know when data was created/modified
    - Debugging: Trace when issues occurred
    - Analytics: Track usage patterns over time
    - Compliance: Meet data retention requirements
    
    Meta:
        abstract = True  # No database table created
        ordering = ['-created_at']  # Newest first by default
    
    Inherited by:
        Course, Lesson, Enrollment, Submission, etc.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when this record was created. Automatically set on creation."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when this record was last updated. Automatically updated on save."
    )
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
    
    def get_age_display(self):
        """
        Return human-readable age of the record.
        
        Example: "Created 2 days ago"
        Useful in admin interfaces and templates.
        """
        from django.utils.timesince import timesince
        return f"Created {timesince(self.created_at)} ago"


class AbstractUserProfile(TimeStampedModel):
    """
    Abstract base model for user profiles (Instructor and Learner).
    
    Why an abstract base?
    Both Instructor and Learner extend Django's User model with additional fields.
    This base class provides common functionality and ensures consistent behavior
    across all user profile types.
    
    Key features:
    1. One-to-one link to Django's built-in User model
    2. Automatic profile creation/deletion signals
    3. Common methods for all profile types
    4. Consistent string representation
    
    Security note:
    We use CASCADE delete to ensure when a User is deleted, their profile
    is automatically removed. This prevents orphaned records.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,  # Makes user_id the primary key
        related_name='%(class)s',  # Creates 'user.instructor' and 'user.learner'
        help_text="Link to Django's built-in User model. One-to-one relationship."
    )
    
    class Meta:
        abstract = True
    
    def __str__(self):
        """Default string representation uses username."""
        return self.user.username
    
    def get_full_name(self):
        """Return user's full name or username if not set."""
        return self.user.get_full_name() or self.user.username
    
    @property
    def email(self):
        """Proxy to user's email for convenience."""
        return self.user.email
    
    @property
    def is_active(self):
        """Proxy to user's active status."""
        return self.user.is_active
    
    class Meta:
        abstract = True