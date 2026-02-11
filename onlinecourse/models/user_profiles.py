"""
User profile models for Instructors and Learners.

These models extend Django's built-in User model to add role-specific fields
and functionality. We use OneToOneField instead of Multi-table inheritance
for better performance and simpler queries.

Architecture decision:
We separate Instructor and Learner into distinct models rather than a single
'Profile' model with a role field. This allows:
1. Different fields per role (full_time for Instructors, occupation for Learners)
2. Type safety - can't accidentally give a Learner instructor-only fields
3. Clear separation of concerns
4. Easier permission management
"""
from django.db import models
from django.conf import settings
from .base import AbstractUserProfile


class Instructor(AbstractUserProfile):
    """
    Instructor profile extending Django User model.
    
    Instructors are content creators and course administrators.
    They create courses, lessons, questions, and grade submissions.
    
    Business logic:
    - full_time: Determines employment status (affects permissions/pay)
    - total_learners: Running total of students taught (for analytics)
    
    Related objects:
    - course_set: All courses this instructor teaches
    - user: Associated Django User (username, password, email)
    """
    
    # ========================================================================
    # EMPLOYMENT FIELDS
    # ========================================================================
    full_time = models.BooleanField(
        default=True,
        help_text="Indicates if instructor is full-time or part-time employee."
    )
    
    hire_date = models.DateField(
        auto_now_add=True,
        help_text="Date when instructor was hired. Automatically set on creation."
    )
    
    # ========================================================================
    # METRICS AND ANALYTICS
    # ========================================================================
    total_learners = models.IntegerField(
        default=0,
        help_text="Cumulative count of unique learners taught by this instructor."
    )
    
    average_rating = models.FloatField(
        default=0.0,
        help_text="Average course rating across all courses taught."
    )
    
    # ========================================================================
    # SPECIALIZATION
    # ========================================================================
    SPECIALIZATION_CHOICES = [
        ('web_dev', 'Web Development'),
        ('data_sci', 'Data Science'),
        ('mobile', 'Mobile Development'),
        ('devops', 'DevOps'),
        ('design', 'UI/UX Design'),
    ]
    
    specialization = models.CharField(
        max_length=20,
        choices=SPECIALIZATION_CHOICES,
        blank=True,
        null=True,
        help_text="Primary teaching area/expertise."
    )
    
    # ========================================================================
    # METHODS
    # ========================================================================
    
    def __str__(self):
        """Return professional display name with title."""
        return f"Instructor: {self.get_full_name()}"
    
    def update_learner_count(self):
        """
        Recalculate total unique learners across all courses.
        
        This is an expensive operation and should be called sparingly,
        perhaps via Celery task or signal handler.
        """
        from .enrollment import Enrollment
        from .course import Course
        
        courses = Course.objects.filter(instructors=self.user)
        unique_learners = Enrollment.objects.filter(
            course__in=courses
        ).values('user').distinct().count()
        
        self.total_learners = unique_learners
        self.save(update_fields=['total_learners'])
    
    @property
    def active_courses(self):
        """Return courses that are currently published."""
        from django.utils import timezone
        from .course import Course
        
        return Course.objects.filter(
            instructors=self.user,
            pub_date__lte=timezone.now()
        )
    
    @property
    def is_full_time(self):
        """Property wrapper for full_time field."""
        return self.full_time


class Learner(AbstractUserProfile):
    """
    Learner profile extending Django User model.
    
    Learners are students who enroll in courses, take exams, and receive grades.
    
    Business logic:
    - occupation: Professional background (affects course recommendations)
    - social_link: Professional profile (LinkedIn, GitHub) for networking
    
    Related objects:
    - enrollment_set: All course enrollments
    - submission_set: All exam submissions
    - user: Associated Django User
    """
    
    # ========================================================================
    # OCCUPATION CHOICES
    # ========================================================================
    STUDENT = 'student'
    DEVELOPER = 'developer'
    DATA_SCIENTIST = 'data_scientist'
    DATABASE_ADMIN = 'dba'
    PRODUCT_MANAGER = 'pm'
    UX_DESIGNER = 'ux'
    
    OCCUPATION_CHOICES = [
        (STUDENT, 'Student - Currently enrolled in academic program'),
        (DEVELOPER, 'Developer - Professional software developer'),
        (DATA_SCIENTIST, 'Data Scientist - ML/AI professional'),
        (DATABASE_ADMIN, 'Database Admin - DBA professional'),
        (PRODUCT_MANAGER, 'Product Manager - Technical PM'),
        (UX_DESIGNER, 'UX Designer - User experience professional'),
    ]
    
    # ========================================================================
    # PROFILE FIELDS
    # ========================================================================
    occupation = models.CharField(
        max_length=20,
        choices=OCCUPATION_CHOICES,
        default=STUDENT,
        help_text="Current professional occupation or student status."
    )
    
    social_link = models.URLField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Professional profile URL (LinkedIn, GitHub, portfolio)."
    )
    
    bio = models.TextField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Short biography or professional summary."
    )
    
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        help_text="Optional: Used for age-restricted content and analytics."
    )
    
    # ========================================================================
    # LEARNING PREFERENCES
    # ========================================================================
    email_notifications = models.BooleanField(
        default=True,
        help_text="Receive email notifications about course activity."
    )
    
    learning_goals = models.TextField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Personal learning objectives and goals."
    )
    
    # ========================================================================
    # METHODS
    # ========================================================================
    
    def __str__(self):
        """Return learner information for admin display."""
        return f"{self.get_full_name()} ({self.get_occupation_display()})"
    
    def enroll(self, course, mode='audit'):
        """
        Enroll this learner in a course.
        
        Args:
            course: Course instance to enroll in
            mode: Enrollment mode (audit/honor/beta)
        
        Returns:
            Enrollment: Created enrollment instance
        
        Raises:
            IntegrityError: If already enrolled
        """
        from .enrollment import Enrollment
        
        enrollment, created = Enrollment.objects.get_or_create(
            user=self.user,
            course=course,
            defaults={'mode': mode}
        )
        
        if created:
            # Update course enrollment counter
            course.total_enrollment += 1
            course.save(update_fields=['total_enrollment'])
        
        return enrollment
    
    @property
    def course_count(self):
        """Return number of courses currently enrolled in."""
        return self.user.enrollment_set.count()
    
    @property
    def completed_courses(self):
        """Return courses where learner has passing grade."""
        # This would need a grade field on Enrollment or Submission
        from .course import Course
        return Course.objects.filter(
            enrollment__user=self.user,
            enrollment__grade__gte=60  # Assuming grade field exists
        )