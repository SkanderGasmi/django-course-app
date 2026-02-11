from django.shortcuts import render
from django.http import HttpResponseRedirect
# <HINT> Import any new Models here
from .models import Course, Enrollment, Question, Choice, Submission  # Added Question, Choice, Submission
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


# <HINT> Create a submit view to create an exam submission record for a course enrollment,
def submit(request, course_id):
    """Submit exam answers and create submission record"""
    # Get user and course object
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    
    # Get the associated enrollment object created when the user enrolled the course
    enrollment = get_object_or_404(Enrollment, user=user, course=course)
    
    # Create a submission object referring to the enrollment
    submission = Submission.objects.create(enrollment=enrollment)
    
    # Collect the selected choices from exam form
    submitted_answers = extract_answers(request)
    
    # Add each selected choice object to the submission object
    for choice_id in submitted_answers:
        choice = get_object_or_404(Choice, pk=choice_id)
        submission.choices.add(choice)
    
    # Redirect to show_exam_result with the submission id
    return redirect('onlinecourse:show_exam_result', course_id=course.id, submission_id=submission.id)



def extract_answers(request):
   submitted_answers = []
   for key in request.POST:
       if key.startswith('choice_'):  # Changed from 'choice' to 'choice_'
           # Extract the choice id from the key name
           choice_id = int(key.split('_')[1])
           submitted_answers.append(choice_id)
   return submitted_answers


# <HINT> Create an exam result view to check if learner passed exam and show their question results
def show_exam_result(request, course_id, submission_id):
    """Show exam results with score and correct/incorrect answers"""
    # Get course and submission based on their ids
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    
    # Get the selected choice ids from the submission record
    selected_choices = submission.choices.all()
    
    # Calculate the total score
    total_score = 0
    max_score = 0
    question_results = []
    
    # For each question in the course
    for question in course.questions.all():
        max_score += question.grade
        
        # Get selected choices for this question
        selected_ids = selected_choices.filter(question=question).values_list('id', flat=True)
        
        # Check if the question was answered correctly using the model method
        is_correct = question.is_get_score(selected_ids)
        if is_correct:
            total_score += question.grade
        
        # Store question result for template
        question_results.append({
            'question': question,
            'is_correct': is_correct,
            'selected_ids': selected_ids,
            'correct_choices': question.choices.filter(is_correct=True),
            'selected_choices': selected_choices.filter(question=question)
        })
    
    # Calculate percentage score
    score_percentage = (total_score / max_score * 100) if max_score > 0 else 0
    
    # Prepare context for rendering
    context = {
        'course': course,
        'submission': submission,
        'score': score_percentage,
        'total_score': total_score,
        'max_score': max_score,
        'question_results': question_results,
        'selected_choices': selected_choices,
    }
    
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)