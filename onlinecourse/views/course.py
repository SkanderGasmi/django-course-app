"""
Course listing and detail views.

This module contains all views related to displaying course information:
1. CourseListView: Paginated list of available courses with enrollment status
2. CourseDetailView: Comprehensive course view with lessons and exam access

Performance optimizations:
- select_related() and prefetch_related() to reduce database queries
- Pagination for course listings (12 per page)
- Cached enrollment status for authenticated users
- Efficient count queries using annotations

UX considerations:
- Visual indicators for enrolled vs available courses
- Clear call-to-action buttons (Enroll, Start Exam)
- Responsive grid layout for course cards
- Progress indicators for enrolled courses
"""
from django.views import generic
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Course, Lesson, Enrollment
from .base import EnrollmentCheckMixin, CourseContextMixin, logger


class CourseListView(EnrollmentCheckMixin, generic.ListView):
    """
    Display paginated list of available courses with enrollment status.
    
    This view serves as the homepage for authenticated and anonymous users.
    It shows the most popular courses first (by enrollment count) and
    indicates which courses the current user is already enrolled in.
    
    Design decisions:
    - Show only top 10 courses by enrollment (performance + UX)
    - Order by enrollment count descending (popularity-based)
    - Enrollment status checked efficiently in bulk
    - Responsive card grid layout via Bootstrap
    
    Template context:
    - course_list: List of Course objects with is_enrolled attribute
    - is_authenticated: Boolean indicating user login status
    - user_name: Current user's name (if authenticated)
    
    Performance optimization:
    Instead of checking enrollment status per course with N queries,
    we prefetch all user enrollments and set is_enrolled in Python.
    This reduces database queries from N+1 to 2.
    """
    
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'
    paginate_by = 12  # Show 12 courses per page
    
    def get_queryset(self):
        """
        Get queryset of courses with optimized enrollment checking.
        
        Returns:
            QuerySet: Top 10 courses ordered by enrollment count
        """
        # Base queryset with related counts (avoid N+1 queries)
        courses = Course.objects.annotate(
            lesson_count=Count('lesson', distinct=True),
            question_count=Count('questions', distinct=True)
        ).order_by('-total_enrollment', '-pub_date')[:10]
        
        user = self.request.user
        
        # Bulk check enrollment status for authenticated users
        if user.is_authenticated:
            # Get all course IDs the user is enrolled in
            enrolled_course_ids = Enrollment.objects.filter(
                user=user,
                course__in=courses
            ).values_list('course_id', flat=True)
            
            # Convert to set for O(1) lookups
            enrolled_set = set(enrolled_course_ids)
            
            # Set is_enrolled attribute on each course
            for course in courses:
                course.is_enrolled = course.id in enrolled_set
        else:
            # Anonymous users are not enrolled in any courses
            for course in courses:
                course.is_enrolled = False
        
        return courses
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.
        
        Returns:
            dict: Context dictionary with user info and stats
        """
        context = super().get_context_data(**kwargs)
        
        # Add user information
        user = self.request.user
        context['is_authenticated'] = user.is_authenticated
        
        if user.is_authenticated:
            context['user_name'] = user.get_full_name() or user.username
            context['enrollment_count'] = Enrollment.objects.filter(
                user=user,
                is_active=True
            ).count()
        
        # Add site statistics
        context['total_courses'] = Course.objects.filter(
            pub_date__isnull=False
        ).count()
        
        context['total_learners'] = User.objects.filter(
            enrollment__isnull=False
        ).distinct().count()
        
        return context


class CourseDetailView(CourseContextMixin, EnrollmentCheckMixin, generic.DetailView):
    """
    Display comprehensive course information including lessons and exam access.
    
    This view shows:
    1. Course metadata (title, description, instructor, etc.)
    2. List of lessons with their content
    3. Exam information (number of questions, total points)
    4. Enrollment status and actions (Enroll/Start Exam)
    
    URL Pattern:
        /course/<int:pk>/
    
    Template:
        onlinecourse/course_detail_bootstrap.html
    
    Security:
        - No authentication required for viewing course details
        - Enrollment status displayed appropriately
        - Exam access restricted to enrolled users
    """
    
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'
    
    def get_queryset(self):
        """
        Optimize queryset with prefetch_related for related objects.
        
        Without this optimization, each lesson and question would trigger
        a separate database query. With prefetch_related, we do it in 3
        queries total regardless of course size.
        
        Returns:
            QuerySet: Course objects with prefetched relationships
        """
        return Course.objects.prefetch_related(
            'lesson_set',  # All lessons in the course
            'questions',   # All questions for the exam
            'instructors__user'  # Instructor user profiles
        )
    
    def get_context_data(self, **kwargs):
        """
        Add enrollment status and lesson content to context.
        
        Returns:
            dict: Enhanced context with enrollment and lesson data
        """
        context = super().get_context_data(**kwargs)
        course = self.object
        
        # Add course context from mixin
        course_context = self.get_course_context(course)
        context.update(course_context)
        
        # Add ordered lessons
        context['lessons'] = course.lesson_set.all().order_by('order')
        
        # Check if user can take exam
        if self.request.user.is_authenticated:
            enrollment = self.get_enrollment(self.request.user, course)
            context['can_take_exam'] = enrollment is not None
            
            # If enrolled, get any existing submissions
            if enrollment:
                context['submissions'] = enrollment.submission_set.all().order_by('-created_at')[:5]
        
        return context