from django.contrib import admin
# <HINT> Import any new Models here
from .models import Course, Lesson, Instructor, Learner, Question, Choice, Submission, Enrollment

# <HINT> Register QuestionInline and ChoiceInline classes here
class ChoiceInline(admin.TabularInline):
    """Choice inline for Question admin"""
    model = Choice
    extra = 3


class QuestionInline(admin.StackedInline):
    """Question inline for Course admin"""
    model = Question
    extra = 2


class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 5


# Register your models here.
class CourseAdmin(admin.ModelAdmin):
    inlines = [LessonInline, QuestionInline]  # Added QuestionInline here
    list_display = ('name', 'pub_date')
    list_filter = ['pub_date']
    search_fields = ['name', 'description']


class LessonAdmin(admin.ModelAdmin):
    list_display = ['title']


# <HINT> Register Question and Choice models here
class QuestionAdmin(admin.ModelAdmin):
    """Question admin with Choice inline"""
    inlines = [ChoiceInline]
    list_display = ['text', 'course', 'grade']
    list_filter = ['course']
    search_fields = ['text']


class SubmissionAdmin(admin.ModelAdmin):
    """Submission admin to view exam submissions"""
    list_display = ['enrollment', 'get_choices', 'get_score']
    list_filter = ['enrollment__course', 'enrollment__user']
    
    def get_choices(self, obj):
        return ", ".join([choice.text[:30] for choice in obj.choices.all()[:3]])
    get_choices.short_description = 'Selected Choices'
    
    def get_score(self, obj):
        # Calculate score for display in admin
        total_score = 0
        max_score = 0
        course = obj.enrollment.course
        
        for question in course.questions.all():
            max_score += question.grade
            selected_ids = obj.choices.filter(question=question).values_list('id', flat=True)
            if question.is_get_score(selected_ids):
                total_score += question.grade
        
        return f"{total_score}/{max_score}"
    get_score.short_description = 'Score'


# Register all models
admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Instructor)
admin.site.register(Learner)
admin.site.register(Enrollment)  # Register Enrollment model
admin.site.register(Question, QuestionAdmin)  # Register Question with custom admin
admin.site.register(Choice)  # Register Choice
admin.site.register(Submission, SubmissionAdmin)  # Register Submission with custom admin