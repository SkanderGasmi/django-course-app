"""
URLs package initializer.
Exports all URL patterns from submodules for inclusion in the main urlpatterns.
This module aggregates patterns from each feature-specific URL module.

Why this approach?
1. Separation of concerns - Each feature manages its own URLs
2. Maintainability - Easy to locate and modify feature-specific routes
3. Scalability - New features add their own URL module without touching others
4. Testability - URL patterns can be tested in isolation
5. Collaboration - Multiple developers can work on different URL modules

Import organization:
1. Base patterns and constants first
2. Feature-specific patterns in logical order
3. Combined urlpatterns for easy inclusion
"""
from django.conf import settings
from django.conf.urls.static import static

# Import URL patterns from feature-specific modules
from .auth import urlpatterns as auth_patterns
from .course import urlpatterns as course_patterns
from .enrollment import urlpatterns as enrollment_patterns
from .exam import urlpatterns as exam_patterns
from .results import urlpatterns as results_patterns

# ============================================================================
# COMBINED URL PATTERNS
# ============================================================================
"""
Master urlpatterns list combining all feature-specific patterns.
This is imported by the root urls.py and includes all application routes.
"""
urlpatterns = []

# Add feature patterns in order of importance/usage
urlpatterns += auth_patterns      # Authentication first (login/registration)
urlpatterns += course_patterns    # Course browsing
urlpatterns += enrollment_patterns # Enrollment actions
urlpatterns += exam_patterns      # Exam submission
urlpatterns += results_patterns   # Exam results

# ============================================================================
# STATIC/MEDIA FILE SERVING (Development only)
# ============================================================================
"""
Serve media files during development.
In production, media files should be served by the web server (nginx, S3, etc.)
"""
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ============================================================================
# EXPORT URLPATTERNS
# ============================================================================
__all__ = ['urlpatterns']