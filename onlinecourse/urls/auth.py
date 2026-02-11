"""
Authentication URL patterns.

This module contains all URL patterns related to user authentication:
- Registration - Create new accounts
- Login - Authenticate existing users
- Logout - Terminate sessions

Why separate authentication URLs?
1. Security - Centralized authentication endpoints for auditing
2. Organization - Clear separation from business logic URLs
3. Reusability - Easy to include in other apps if needed
4. Testing - Isolated testing of auth flows
"""
from django.urls import path
from .. import views
from .base import (
    REGISTRATION_URL,
    LOGIN_URL,
    LOGOUT_URL
)

# ============================================================================
# AUTHENTICATION URL PATTERNS
# ============================================================================
"""
All authentication endpoints follow REST conventions:
- GET: Display form
- POST: Process form submission
- No resource IDs (operate on current user)
"""
urlpatterns = [
    # User Registration
    # URL: /onlinecourse/registration/
    # Methods: GET (form), POST (create user)
    path(
        route='registration/',
        view=views.registration_request,
        name=REGISTRATION_URL
    ),
    
    # User Login
    # URL: /onlinecourse/login/
    # Methods: GET (form), POST (authenticate)
    path(
        route='login/',
        view=views.login_request,
        name=LOGIN_URL
    ),
    
    # User Logout
    # URL: /onlinecourse/logout/
    # Methods: GET (logout and redirect)
    path(
        route='logout/',
        view=views.logout_request,
        name=LOGOUT_URL
    ),
]

# ============================================================================
# URL PATTERN SUMMARY
# ============================================================================
"""
┌─────────────┬─────────────────────────────┬─────────────────────────┐
│ Name        │ Pattern                    │ Purpose                 │
├─────────────┼─────────────────────────────┼─────────────────────────┤
│ registration│ /registration/             │ New user registration   │
│ login       │ /login/                   │ User authentication     │
│ logout      │ /logout/                  │ Session termination     │
└─────────────┴─────────────────────────────┴─────────────────────────┘
"""