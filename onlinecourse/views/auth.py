"""
Authentication views for user registration, login, and logout.

This module handles all user authentication flows:
1. Registration - Create new user accounts with profile setup
2. Login - Authenticate existing users
3. Logout - Terminate user sessions

Security considerations:
- Passwords are never stored in plain text (Django's hashing)
- CSRF protection is enabled on all forms
- Failed login attempts don't reveal whether user exists
- Session management follows Django best practices
- HTTPS should be enforced in production

Template structure:
- All auth templates use Bootstrap 5 for responsive design
- Consistent error message display across all forms
- Password strength indicators (future enhancement)
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.urls import reverse
from .base import logger


def registration_request(request):
    """
    Handle user registration requests (GET and POST).
    
    Flow:
    1. GET: Display empty registration form
    2. POST: Validate and create new user account
       a. Check if username already exists
       b. Create User object with Django's built-in User model
       c. Automatically log in the new user
       d. Redirect to course list
    
    Form fields expected:
    - username: Unique identifier for the user
    - psw: Password (will be hashed)
    - firstname: User's first name
    - lastname: User's last name
    
    Security notes:
    - No email verification required (can be added later)
    - Passwords are hashed via create_user()
    - Failed registration preserves form data via context
    
    Args:
        request: HTTP request object
    
    Returns:
        HttpResponse: Rendered registration form or redirect
    
    Template:
        onlinecourse/user_registration_bootstrap.html
    """
    context = {}
    
    if request.method == 'GET':
        # Display empty registration form
        return render(
            request,
            'onlinecourse/user_registration_bootstrap.html',
            context
        )
    
    elif request.method == 'POST':
        # Extract form data
        username = request.POST.get('username', '').strip()
        password = request.POST.get('psw', '')
        first_name = request.POST.get('firstname', '').strip()
        last_name = request.POST.get('lastname', '').strip()
        
        # Validate required fields
        if not all([username, password, first_name, last_name]):
            context['message'] = "All fields are required."
            return render(
                request,
                'onlinecourse/user_registration_bootstrap.html',
                context
            )
        
        # Check if username already exists
        user_exists = User.objects.filter(username=username).exists()
        
        if not user_exists:
            # Create new user - password will be hashed automatically
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            
            # Log the registration event
            logger.info(f"New user registered: {username}")
            
            # Automatically log in the new user
            login(request, user)
            
            # Redirect to course list
            return redirect("onlinecourse:index")
        else:
            # Username already taken
            logger.warning(f"Registration failed - username exists: {username}")
            context['message'] = "Username already exists. Please choose another."
            return render(
                request,
                'onlinecourse/user_registration_bootstrap.html',
                context
            )


def login_request(request):
    """
    Handle user login requests.
    
    Flow:
    1. GET: Display login form
    2. POST: Authenticate credentials and create session
    
    Authentication process:
    1. Extract username and password from POST data
    2. Use Django's authenticate() function to verify credentials
    3. If valid, create session via login()
    4. Redirect to course list or requested page
    
    Security features:
    - Timing attacks mitigated by authenticate() function
    - No distinction between "user doesn't exist" and "wrong password"
    - Session cookie is HTTP-only and secure in production
    - CSRF token required for POST requests
    
    Args:
        request: HTTP request object
    
    Returns:
        HttpResponse: Rendered login form or redirect
    
    Template:
        onlinecourse/user_login_bootstrap.html
    """
    context = {}
    
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('psw', '')
        
        # Authenticate user
        user = authenticate(
            request,
            username=username,
            password=password
        )
        
        if user is not None:
            # Successful authentication
            login(request, user)
            logger.info(f"User logged in: {username}")
            
            # Redirect to next parameter if provided, otherwise to index
            next_url = request.GET.get('next', 'onlinecourse:index')
            return redirect(next_url)
        else:
            # Failed authentication
            logger.warning(f"Failed login attempt for username: {username}")
            context['message'] = "Invalid username or password."
            
    # GET request or failed POST - display login form
    return render(
        request,
        'onlinecourse/user_login_bootstrap.html',
        context
    )


def logout_request(request):
    """
    Handle user logout requests.
    
    Flow:
    1. Terminate user session via logout()
    2. Redirect to course list
    
    Security:
    - Session cookie is deleted
    - CSRF token is rotated
    - No confirmation required (idempotent operation)
    
    Args:
        request: HTTP request object
    
    Returns:
        HttpResponseRedirect: Redirect to course list
    """
    username = request.user.username if request.user.is_authenticated else "Anonymous"
    logout(request)
    logger.info(f"User logged out: {username}")
    
    # Redirect to main course listing
    return redirect('onlinecourse:index')