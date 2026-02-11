"""
Course admin configuration.
Manages the Course model and its related Lesson/Question inlines.
This is the primary admin interface for course creators.
"""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from ..models import Course, Lesson, Question
from .base import TimestampedAdminMixin


class LessonInline(admin.StackedInline):
    """
    Inline admin for managing Lessons within a Course.
    
    Why StackedInline? Lessons have longer descriptive content (titles,
    descriptions, video URLs) that benefits from a vertical layout with
    more space. Each lesson is a significant content block.
    
    Design decisions:
    - extra=1: Show one empty form by default to encourage incremental addition
    - show_change_link=True: Allow editing lessons separately for complex content
    - fields ordering: Most important fields first (title before metadata)
    """
    model = Lesson
    extra = 1  # Start with 1 empty form to reduce visual clutter
    show_change_link = True  # Enable deep edit navigation
    fields = ['title', 'description', 'video_url']  # Explicit ordering
    
    def get_extra(self, request, obj=None, **kwargs):
        """
        Dynamically determine number of extra forms.
        
        Why? When creating a new course, show more empty forms to encourage
        content creation. When editing existing, show fewer to keep it clean.
        
        Args:
            request: HTTP request object
            obj: Current course object (None for add form)
        """
        if obj is None:  # Adding new course
            return 3  # Encourage adding multiple lessons upfront
        return 1  # Editing existing - add one at a time


class QuestionInline(admin.TabularInline):
    """
    Inline admin for managing Questions within a Course.
    
    Why TabularInline? Questions are data-dense objects with numeric grades.
    Tabular format allows quick scanning of questions and their point values
    in a compact table format, similar to a spreadsheet.
    
    Trade-off: Limited space for question text, but we provide truncation
    in list display. Consider StackedInline if questions become very long.
    """
    model = Question
    extra = 1
    show_change_link = True
    fields = ['text', 'grade']  # Keep it simple in course context
    
    def get_queryset(self, request):
        """
        Optimize queryset with select_related.
        
        Why? Each question might have choices we display. This prefetches
        related data to avoid N+1 queries when rendering the inline.
        """
        return super().get_queryset(request).select_related('course')


class CourseAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    """
    Comprehensive admin interface for Course management.
    
    This is the flagship admin interface for the online course platform.
    Instructors and administrators use this to create and manage entire
    courses, including their lessons and questions in one unified view.
    
    Key features:
    1. Integrated lesson and question management via inlines
    2. Performance metrics (lesson/question counts)
    3. Frontend preview links for quality assurance
    4. Advanced filtering and search capabilities
    5. Audit trail via timestamp mixin
    """
    
    # ========================================================================
    # LAYOUT CONFIGURATION
    # ========================================================================
    inlines = [LessonInline, QuestionInline]
    
    # ========================================================================
    # LIST VIEW CONFIGURATION
    # ========================================================================
    list_display = [
        'name',
        'pub_date', 
        'total_lessons',
        'total_questions',
        'total_points',
        'course_preview_link',
        'is_published_indicator'
    ]
    
    list_filter = [
        'pub_date',
        ('instructors', admin.RelatedOnlyFieldListFilter),  # Better than default
    ]
    
    search_fields = [
        'name',
        'description',
        'instructors__username',  # Allow searching by instructor name
    ]
    
    date_hierarchy = 'pub_date'  # Enables date drill-down navigation
    list_select_related = ['instructors']  # Optimize query performance
    
    # ========================================================================
    # FORM CONFIGURATION
    # ========================================================================
    fieldsets = [
        (
            'Basic Information',  # Most important fields first
            {
                'fields': ['name', 'description', 'pub_date'],
                'description': 'Core course details displayed to students'
            }
        ),
        (
            'Instructors',  # Secondary but crucial
            {
                'fields': ['instructors'],
                'description': 'Select one or more instructors for this course',
                'classes': ['wide']  # Give more space for multi-select
            }
        ),
        (
            'Advanced Options',  # Rarely changed settings
            {
                'fields': ['total_enrollment'],  # Assuming this field exists
                'classes': ['collapse'],  # Hide by default to reduce clutter
                'description': 'These settings rarely need adjustment'
            }
        ),
    ]
    
    # ========================================================================
    # CUSTOM METHODS (Derived/Computed Fields)
    # ========================================================================
    
    def total_lessons(self, obj):
        """
        Calculate and display total number of lessons in the course.
        
        Why count() not len()? .count() performs a SQL COUNT which is
        more efficient than len() which loads all objects into memory.
        
        Returns:
            int: Number of lessons with HTML badge styling
        """
        count = obj.lesson_set.count()
        color = 'green' if count > 5 else 'orange' if count > 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, count
        )
    total_lessons.short_description = '📚 Lessons'
    total_lessons.admin_order_field = 'lesson__count'  # Enable sorting
    
    def total_questions(self, obj):
        """
        Calculate total questions across all lessons (or directly in course).
        """
        count = obj.questions.count()
        return format_html(
            '<span style="color: {};">{}</span>',
            'blue' if count > 0 else 'gray',
            count
        )
    total_questions.short_description = '❓ Questions'
    
    def total_points(self, obj):
        """
        Sum of all question grades (total possible score).
        
        This helps instructors quickly assess exam difficulty.
        """
        total = obj.questions.aggregate(total=models.Sum('grade'))['total'] or 0
        return f"{total} pts"
    total_points.short_description = '🏆 Total Points'
    
    def course_preview_link(self, obj):
        """
        Generate frontend preview link for quality assurance.
        
        Why try/except? URL reversing can fail if URL patterns change.
        We gracefully degrade rather than crashing the admin interface.
        
        Returns:
            HTML anchor tag with course preview URL
        """
        try:
            url = reverse('onlinecourse:course_details', args=[obj.id])
            return format_html(
                '<a href="{}" target="_blank" style="background: #f0f0f0; '
                'padding: 3px 8px; border-radius: 3px; text-decoration: none;">'
                '🔍 Preview</a>',
                url
            )
        except:
            return "⚠️ No preview available"
    course_preview_link.short_description = 'View'
    
    def is_published_indicator(self, obj):
        """
        Visual indicator if course is published (based on pub_date).
        
        Assumes courses are published if pub_date is in the past.
        Consider adding explicit is_published boolean field.
        """
        from django.utils import timezone
        is_published = obj.pub_date <= timezone.now()
        return format_html(
            '<span style="color: {};">●</span> {}',
            'green' if is_published else 'orange',
            'Published' if is_published else 'Scheduled'
        )
    is_published_indicator.short_description = 'Status'
    
    # ========================================================================
    # PERMISSIONS & BEHAVIOR OVERRIDES
    # ========================================================================
    
    def save_model(self, request, obj, form, change):
        """
        Override save to add the current user as instructor for new courses.
        
        Why? When an instructor creates a course through admin, they should
        automatically be added as an instructor. This prevents orphaned courses
        with no instructors.
        
        Args:
            request: HTTP request (contains user)
            obj: Course instance being saved
            form: ModelForm instance
            change: Boolean (True if editing, False if creating)
        """
        super().save_model(request, obj, form, change)
        
        if not change:  # Only on creation
            # Check if user is an Instructor instance
            try:
                instructor = request.user.instructor
                obj.instructors.add(instructor)
            except:
                # User isn't an Instructor, skip auto-assignment
                pass
    
    def get_queryset(self, request):
        """
        Optimize queryset with prefetch_related for counts.
        
        Without this, each course in list view would make additional queries
        for lesson and question counts. With prefetch, we do it in 2 queries
        total regardless of course count.
        """
        return super().get_queryset(request).prefetch_related(
            'lesson_set',
            'questions'
        )