"""
Django admin registration module.

This file is intentionally minimal - it just imports the admin classes
from our well-organized package structure and registers them with the admin site.

Why this approach?
1. Separation of concerns: Each admin class has its own file
2. Maintainability: Easy to locate and edit specific admin configurations
3. Testability: Can test admin classes in isolation
4. Collaboration: Multiple developers can work on different admin files
5. Performance: Only load what's needed
"""
from django.contrib import admin
from .models import (
    Course, Lesson, Instructor, Learner, 
    Question, Choice, Submission, Enrollment
)

# Import all admin classes from our organized package
from .admin import (
    CourseAdmin,
    LessonAdmin,
    QuestionAdmin,
    EnrollmentAdmin, 
    SubmissionAdmin,
    LearnerAdmin,
    InstructorAdmin
)

# ============================================================================
# MODEL REGISTRATION
# ============================================================================
# Each model is registered with its corresponding custom admin class.
# Models without custom admin use default registration (Choice in this case).

admin.site.register(Course, CourseAdmin)        # Complete course management
admin.site.register(Lesson, LessonAdmin)        # Individual lesson management
admin.site.register(Question, QuestionAdmin)    # Assessment question management
admin.site.register(Choice)                     # Simple model, default admin is sufficient
admin.site.register(Submission, SubmissionAdmin) # Exam submission review
admin.site.register(Enrollment, EnrollmentAdmin) # Student enrollment management
admin.site.register(Instructor, InstructorAdmin) # Instructor profile management
admin.site.register(Learner, LearnerAdmin)       # Learner profile management

# ============================================================================
# ADMIN SITE CUSTOMIZATION
# ============================================================================
# These settings customize the overall Django admin interface branding.

admin.site.site_header = 'Online Course Learning Platform Administration'
"""
Header displayed at the top of every admin page.
Changed from default "Django Administration" to our platform name.
"""

admin.site.site_title = 'Course Admin'
"""
Browser tab title for admin pages.
"""

admin.site.index_title = 'Course Management Dashboard'
"""
Title displayed on the main admin index page.
"""

# ============================================================================
# OPTIONAL: DISABLE DEFAULT MODELS
# ============================================================================
# If you want to hide Django's default models (Groups, Users) from the admin:
# admin.site.unregister(Group)
# admin.site.unregister(User)