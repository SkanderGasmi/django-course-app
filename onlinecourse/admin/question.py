"""
Question and Choice admin configuration.
Manages the assessment system including questions and their answer choices.
This is critical for maintaining exam integrity and grading logic.
"""
from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from ..models import Question, Choice
from .base import ExportCSVMixin


class ChoiceInline(admin.TabularInline):
    """
    Inline admin for managing answer choices within a question.
    
    Why TabularInline? Choices are simple key-value pairs (text + correctness flag)
    that benefit from a compact, spreadsheet-like interface. This allows instructors
    to quickly add multiple choices and mark correct ones.
    
    Critical design: We limit extra to 4 because multiple-choice questions typically
    have 4-5 options. Showing more than 4 empty forms would waste space.
    
    Note: The order of choices matters! Django preserves the order they're saved,
    which is why we don't add ordering here unless the model has an 'order' field.
    """
    model = Choice
    extra = 4  # Standard multiple choice has 4 options
    max_num = 10  # Prevent excessive choices that could overwhelm students
    
    # Customize which fields appear and in what order
    fields = ['text', 'is_correct']
    
    # Add CSS classes for visual distinction
    classes = ['collapse']  # Initially collapsed to reduce visual clutter
    
    def get_formset(self, request, obj=None, **kwargs):
        """
        Customize formset behavior based on context.
        
        When creating a new question, show all 4 empty forms.
        When editing existing, only show 1 extra form.
        This respects the principle of least surprise.
        """
        formset = super().get_formset(request, obj, **kwargs)
        if obj is not None:  # Editing existing
            formset.extra = 1
        return formset


class QuestionAdmin(ExportCSVMixin, admin.ModelAdmin):
    """
    Comprehensive admin for managing assessment questions.
    
    This interface is used by instructors to create exam questions and
    define correct answers. It's crucial to the learning assessment system.
    
    Key considerations:
    1. Data integrity: Ensure each question has at least one correct answer
    2. Performance: Optimize for questions with many choices
    3. UX: Make it easy to identify correct answers at a glance
    4. Analytics: Provide insights into question difficulty/usage
    
    Security: All input is sanitized via Django's form system.
    """
    
    # ========================================================================
    # BASIC CONFIGURATION
    # ========================================================================
    inlines = [ChoiceInline]
    
    # ========================================================================
    # LIST VIEW CONFIGURATION
    # ========================================================================
    list_display = [
        'id_display',
        'question_preview',
        'course_link',
        'grade_badge',
        'choice_count_display',
        'correct_answer_preview',
        'difficulty_indicator',
    ]
    
    list_display_links = ['id_display', 'question_preview']  # Which fields are clickable
    
    list_filter = [
        'course',
        'grade',
        ('choice__is_correct', admin.BooleanFieldListFilter),  # Filter by if question HAS correct answers
    ]
    
    search_fields = [
        'text',
        'course__name',
        'choice__text',  # Allow searching by answer text
    ]
    
    list_select_related = ['course']  # Prevent N+1 queries
    
    # ========================================================================
    # FORM CONFIGURATION
    # ========================================================================
    fieldsets = [
        (
            'Question Content',
            {
                'fields': ['course', 'text'],
                'description': 'The actual question text displayed to students'
            }
        ),
        (
            'Grading',
            {
                'fields': ['grade'],
                'description': 'Point value for this question',
                'classes': ['wide']
            }
        ),
    ]
    
    # ========================================================================
    # EXPORT CONFIGURATION (from ExportCSVMixin)
    # ========================================================================
    export_fields = ['id', 'course__name', 'text', 'grade']
    export_filename = 'questions_export.csv'
    
    # ========================================================================
    # CUSTOM DISPLAY METHODS
    # ========================================================================
    
    def id_display(self, obj):
        """
        Display question ID with visual formatting.
        
        Returns:
            Formatted ID badge
        """
        return format_html(
            '<span style="background: #e3f2fd; padding: 2px 8px; '
            'border-radius: 10px; font-family: monospace;">Q{}</span>',
            obj.id
        )
    id_display.short_description = 'ID'
    id_display.admin_order_field = 'id'
    
    def question_preview(self, obj):
        """
        Truncate long questions for list view readability.
        
        Why truncate? Admin list view is for scanning, not reading full text.
        We preserve the full text in the detail view.
        
        Args:
            obj: Question instance
            
        Returns:
            str: Truncated question text with ellipsis if needed
        """
        if len(obj.text) > 80:
            return f"{obj.text[:80]}..."
        return obj.text
    question_preview.short_description = 'Question'
    question_preview.admin_order_field = 'text'
    
    def course_link(self, obj):
        """
        Link to the associated course admin.
        
        This enables quick navigation between question and its parent course.
        """
        try:
            url = reverse('admin:onlinecourse_course_change', args=[obj.course.id])
            return format_html('<a href="{}">{}</a>', url, obj.course.name)
        except:
            return obj.course.name
    course_link.short_description = 'Course'
    course_link.admin_order_field = 'course__name'
    
    def grade_badge(self, obj):
        """
        Visual representation of question point value.
        
        Color coding helps instructors quickly identify high-stakes questions.
        """
        if obj.grade >= 10:
            color = '#c62828'  # Red for high value
            icon = '🔴'
        elif obj.grade >= 5:
            color = '#ef6c00'  # Orange for medium
            icon = '🟠'
        else:
            color = '#2e7d32'  # Green for low
            icon = '🟢'
            
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.grade
        )
    grade_badge.short_description = 'Points'
    grade_badge.admin_order_field = 'grade'
    
    def choice_count_display(self, obj):
        """
        Count choices and highlight if missing correct answers.
        
        Critical: Questions without correct answers are invalid and will
        break the grading system. We visually flag these.
        """
        choice_count = obj.choice_set.count()
        correct_count = obj.choice_set.filter(is_correct=True).count()
        
        if correct_count == 0:
            # RED ALERT - No correct answer!
            return format_html(
                '<span style="color: #c62828; font-weight: bold;">⚠️ {} (0 correct!)</span>',
                choice_count
            )
        elif correct_count > 1:
            # Warning - Multiple correct answers
            return format_html(
                '<span style="color: #ef6c00;">{} ({} correct)</span>',
                choice_count, correct_count
            )
        else:
            # Perfect - exactly one correct answer
            return format_html(
                '<span style="color: #2e7d32;">✅ {} choices</span>',
                choice_count
            )
    choice_count_display.short_description = 'Choices'
    choice_count_display.admin_order_field = 'choice__count'
    
    def correct_answer_preview(self, obj):
        """
        Display the correct answer text for quick reference.
        
        This is a huge time-saver for instructors reviewing questions.
        """
        correct_choices = obj.choice_set.filter(is_correct=True)[:2]  # Limit to 2
        
        if not correct_choices:
            return format_html('<span style="color: #c62828;">❌ No correct answer!</span>')
        
        previews = []
        for choice in correct_choices:
            if len(choice.text) > 30:
                previews.append(f"{choice.text[:30]}...")
            else:
                previews.append(choice.text)
        
        preview = ", ".join(previews)
        remaining = obj.choice_set.filter(is_correct=True).count() - 2
        
        if remaining > 0:
            preview += f" (+{remaining} more)"
            
        return format_html(
            '<span style="color: #2e7d32;">✓ {}</span>',
            preview
        )
    correct_answer_preview.short_description = 'Correct Answer(s)'
    
    def difficulty_indicator(self, obj):
        """
        Estimate question difficulty based on submission statistics.
        
        This requires the Submission model to be populated. Shows N/A if
        no submissions exist yet.
        
        Returns:
            HTML span with difficulty rating
        """
        try:
            from ..models import Submission
            
            # Get all submissions that include this question
            submissions = Submission.objects.filter(choices__question=obj).distinct()
            
            if not submissions.exists():
                return format_html('<span style="color: #757575;">📊 No data</span>')
            
            # Calculate success rate
            correct_count = 0
            for submission in submissions:
                selected_ids = submission.choices.filter(question=obj).values_list('id', flat=True)
                if obj.is_get_score(list(selected_ids)):
                    correct_count += 1
            
            success_rate = (correct_count / submissions.count()) * 100
            
            if success_rate >= 80:
                return format_html('<span style="color: #2e7d32;">✅ Easy ({:.0f}%)</span>', success_rate)
            elif success_rate >= 50:
                return format_html('<span style="color: #ef6c00;">⚠️ Medium ({:.0f}%)</span>', success_rate)
            else:
                return format_html('<span style="color: #c62828;">🔴 Hard ({:.0f}%)</span>', success_rate)
        except:
            return format_html('<span style="color: #757575;">📊 N/A</span>')
    difficulty_indicator.short_description = 'Difficulty'
    
    # ========================================================================
    # CUSTOM ACTIONS
    # ========================================================================
    
    actions = ['duplicate_question', 'set_grade_to_5', 'export_as_csv']
    
    def duplicate_question(self, request, queryset):
        """
        Create copies of selected questions.
        
        Useful for creating variations of similar questions.
        
        Note: This creates new question objects with "Copy of " prefix.
        """
        for question in queryset:
            # Create new question
            new_question = Question.objects.create(
                course=question.course,
                text=f"Copy of {question.text[:70]}",  # Truncate to avoid too long
                grade=question.grade
            )
            
            # Copy all choices
            for choice in question.choice_set.all():
                Choice.objects.create(
                    question=new_question,
                    text=choice.text,
                    is_correct=choice.is_correct
                )
        
        self.message_user(
            request,
            f"Successfully duplicated {queryset.count()} question(s)."
        )
    duplicate_question.short_description = "📋 Duplicate selected questions"
    
    def set_grade_to_5(self, request, queryset):
        """Quick action to standardize question point values."""
        updated = queryset.update(grade=5)
        self.message_user(request, f"Updated {updated} questions to 5 points.")
    set_grade_to_5.short_description = "🎯 Set grade to 5 points"
    
    # ========================================================================
    # FORM VALIDATION
    # ========================================================================
    
    def save_related(self, request, form, formsets, change):
        """
        Ensure every question has at least one correct answer.
        
        This validation runs after saving the question and its choices.
        If no correct answer exists, we default the first choice to correct.
        
        This prevents a common data integrity issue.
        """
        super().save_related(request, form, formsets, change)
        
        obj = form.instance
        if not obj.choice_set.filter(is_correct=True).exists():
            first_choice = obj.choice_set.first()
            if first_choice:
                first_choice.is_correct = True
                first_choice.save()
                self.message_user(
                    request,
                    f"⚠️ Question #{obj.id} had no correct answer. "
                    f"Defaulted first choice to correct.",
                    level='WARNING'
                )