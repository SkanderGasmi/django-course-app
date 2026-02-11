"""
Course browsing and detail URL patterns.

This module contains URL patterns for viewing course information:
- Index/Homepage - List of available courses
- Course Detail - Comprehensive course view

Design principles:
1. RESTful - Resource-based URLs
2. Hierarchical - Course details nested under course resource
3. Semantic - URLs reflect content structure
4. SEO-friendly - Clean, readable URLs
"""
from django.urls import path
from .. import views
from .base import (
    PK_PARAM,
    INDEX_URL,
    COURSE_DETAIL_URL
)

# ============================================================================
# COURSE URL PATTERNS
# ============================================================================
"""
Course endpoints follow RESTful conventions:
- Collection: / (course list)
- Resource: /<id>/ (single course)
"""
urlpatterns = [
    # Course List (Homepage)
    # URL: /onlinecourse/
    # Methods: GET
    # View: CourseListView - Displays paginated course grid
    path(
        route='',
        view=views.CourseListView.as_view(),
        name=INDEX_URL
    ),
    
    # Course Detail
    # URL: /onlinecourse/<int:pk>/
    # Methods: GET
    # View: CourseDetailView - Shows course content and exam info
    # Parameter: pk - Primary key of the course
    path(
        route=f'<int:{PK_PARAM}>/',
        view=views.CourseDetailView.as_view(),
        name=COURSE_DETAIL_URL
    ),
]

# ============================================================================
# URL PATTERN SUMMARY
# ============================================================================
"""
┌──────────────┬─────────────────┬──────────────────────────────┐
│ Name         │ Pattern        │ Purpose                      │
├──────────────┼─────────────────┼──────────────────────────────┤
│ index        │ /              │ Course listing homepage      │
│ course_details│ /<pk>/       │ Individual course page       │
└──────────────┴─────────────────┴──────────────────────────────┘

Examples:
- /onlinecourse/          → All courses
- /onlinecourse/42/       → Course with ID 42
"""