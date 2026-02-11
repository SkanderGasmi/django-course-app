"""
Django URL configuration for the onlinecourse application.

This file is intentionally minimal - it simply imports the combined urlpatterns
from our modular urls package. This maintains compatibility with Django's
URL resolution system while allowing us to maintain a clean, modular structure.

Why keep this file?
1. Django expects a urls.py at the app root
2. Maintains backward compatibility
3. Simple - One line import
4. Clear - Shows that URLs are modularized

The actual URL patterns are defined in:
- urls/auth.py     - Authentication endpoints
- urls/course.py   - Course browsing endpoints
- urls/enrollment.py - Enrollment endpoints
- urls/exam.py     - Exam submission endpoints
- urls/results.py  - Exam results endpoints
"""
from .urls import urlpatterns

# ============================================================================
# EXPORT URLPATTERNS
# ============================================================================
# Django's URL resolver imports urlpatterns from this module
__all__ = ['urlpatterns']