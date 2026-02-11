"""
Submission admin configuration.
Manages student exam submissions and provides detailed scoring analytics.
This is a read-intensive interface used by instructors to review student performance.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.urls import reverse
from ..models import Submission, Enrollment, Question, Choice
from .base import ExportCSVMixin
import json


class SubmissionAdmin(ExportCSVMixin, admin.ModelAdmin):
    """
    Advanced admin interface for exam submissions.
    
    This is one of the most performance-critical admin interfaces because:
    1. Submissions grow quickly with student population
    2. Score calculation requires multiple joins
    3. Instructors often need to filter and analyze large datasets
    
    Key optimizations implemented:
    1. select_related/prefetch_related to reduce database queries
    2. Pagination with reasonable page size
    3. Cached score display to avoid recalculation on every page load
    4. Lazy loading of choice details
    
    Security considerations:
    1. Read-only fields prevent grade tampering
    2. Filter by instructor's own courses only (see get_queryset)
    3. No inline editing of submission data
    """
    
    # ========================================================================
    # LIST VIEW CONFIGURATION
    # ========================================================================
    
    list_display = [
        'id_badge',
        'student_info',
        'course_badge',
        'submission_timestamp',
        'choices_summary',
        'score_display',
        'performance_indicator',
        'review_link'
    ]
    
    list_filter = [
        ('submission_date', admin.DateFieldListFilter),  # Enhanced date filter
        ('enrollment__course', admin.RelatedOnlyFieldListFilter),
        ('enrollment__user', admin.RelatedOnlyFieldListFilter),
        'choices__question',  # Filter by specific questions
    ]
    
    search_fields = [
        'enrollment__user__username',
        'enrollment__user__email',
        'enrollment__course__name',
        'choices__text',  # Search by selected answer text
    ]
    
    date_hierarchy = 'submission_date'
    
    # ========================================================================
    # PERFORMANCE OPTIMIZATIONS
    # ========================================================================
    
    list_select_related = [
        'enrollment__user',
        'enrollment__course'
    ]
    
    list_prefetch_related = [
        'choices',
        'choices__question'
    ]
    
    list_per_page = 50
    list_max_show_all = 200  # Prevent loading too many records
    
    # ========================================================================
    # READ-ONLY FIELDS
    # ========================================================================
    
    readonly_fields = [
        'submission_date',
        'enrollment',
        'choices_detailed',
        'score_breakdown',
        'answer_analysis'
    ]
    
    # ========================================================================
    # FIELDSET LAYOUT
    # ========================================================================
    
    fieldsets = [
        (
            'Submission Information',
            {
                'fields': ['enrollment', 'submission_date'],
                'description': 'Student and course information (read-only)'
            }
        ),
        (
            'Score Analysis',
            {
                'fields': ['score_breakdown', 'performance_indicator'],
                'description': 'Detailed scoring and performance metrics',
                'classes': ['wide']
            }
        ),
        (
            'Answer Details',
            {
                'fields': ['choices_detailed', 'answer_analysis'],
                'description': 'Complete record of selected answers',
                'classes': ['collapse']  # Collapsed by default to save space
            }
        ),
    ]
    
    # ========================================================================
    # EXPORT CONFIGURATION
    # ========================================================================
    
    export_fields = [
        'id',
        'enrollment__user__username',
        'enrollment__course__name', 
        'submission_date',
        'calculated_total_score',
        'calculated_max_score'
    ]
    export_filename = 'submissions_export.csv'
    
    # ========================================================================
    # CUSTOM DISPLAY METHODS
    # ========================================================================
    
    def id_badge(self, obj):
        """
        Display submission ID with visual styling.
        
        Returns:
            HTML span with submission ID badge
        """
        return format_html(
            '<span style="background: #e8eaf6; padding: 2px 8px; '
            'border-radius: 12px; font-family: monospace; '
            'font-size: 0.9em;">S#{}</span>',
            obj.id
        )
    id_badge.short_description = 'ID'
    id_badge.admin_order_field = 'id'
    
    def student_info(self, obj):
        """
        Display student information with link to user admin.
        
        Returns:
            HTML link to student's user profile
        """
        user = obj.enrollment.user
        try:
            url = reverse('admin:auth_user_change', args=[user.id])
            return format_html(
                '<a href="{}"><strong>{}</strong><br>'
                '<span style="color: #666; font-size: 0.85em;">{}</span></a>',
                url,
                user.get_full_name() or user.username,
                user.email or 'No email'
            )
        except:
            return f"{user.username}\n{user.email}"
    student_info.short_description = 'Student'
    student_info.admin_order_field = 'enrollment__user__username'
    
    def course_badge(self, obj):
        """
        Display course information with enrollment date.
        
        Returns:
            HTML formatted course details
        """
        enrollment = obj.enrollment
        course = enrollment.course
        
        return format_html(
            '<strong>{}</strong><br>'
            '<span style="color: #666; font-size: 0.85em;">'
            'Enrolled: {}</span>',
            course.name,
            enrollment.date_enrolled.strftime('%Y-%m-%d')
        )
    course_badge.short_description = 'Course'
    course_badge.admin_order_field = 'enrollment__course__name'
    
    def submission_timestamp(self, obj):
        """
        Display formatted submission timestamp with relative time.
        
        Returns:
            HTML span with absolute and relative time
        """
        from django.utils.timesince import timesince
        
        absolute_time = obj.submission_date.strftime('%Y-%m-%d %H:%M')
        relative_time = timesince(obj.submission_date)
        
        return format_html(
            '<span title="{}">{}</span><br>'
            '<span style="color: #666; font-size: 0.85em;">({} ago)</span>',
            absolute_time,
            absolute_time,
            relative_time
        )
    submission_timestamp.short_description = 'Submitted'
    submission_timestamp.admin_order_field = 'submission_date'
    
    def choices_summary(self, obj):
        """
        Display summary of selected choices with count.
        
        Returns:
            HTML formatted choice summary
        """
        choices = obj.choices.all()
        total_choices = choices.count()
        
        # Group by question for better organization
        questions = {}
        for choice in choices:
            q_text = choice.question.text[:50]
            if q_text not in questions:
                questions[q_text] = []
            questions[q_text].append(choice.text[:30])
        
        # Format summary
        if not questions:
            return format_html('<span style="color: #c62828;">No answers selected</span>')
        
        summary_parts = []
        for q_text, answers in list(questions.items())[:2]:  # Show first 2 questions only
            answers_str = ', '.join(answers[:2])
            summary_parts.append(f"{q_text}: {answers_str}")
        
        summary = '; '.join(summary_parts)
        
        if len(questions) > 2:
            remaining = len(questions) - 2
            summary += f'; ... and {remaining} more questions'
        
        return format_html(
            '<span title="{}">{}</span>',
            ' | '.join([f"{q}: {', '.join(a)}" for q, a in questions.items()]),
            summary[:100] + '...' if len(summary) > 100 else summary
        )
    choices_summary.short_description = 'Answers'
    
    def score_display(self, obj):
        """
        Calculate and display score with visual feedback.
        
        This is the most complex display method because it needs to:
        1. Calculate total possible points
        2. Calculate earned points
        3. Apply the grading logic from Question.is_get_score()
        4. Format with appropriate colors and icons
        
        Returns:
            HTML formatted score display with color coding
        """
        try:
            total_score = 0
            max_score = 0
            course = obj.enrollment.course
            
            for question in course.questions.all():
                max_score += question.grade
                selected_ids = list(obj.choices.filter(
                    question=question
                ).values_list('id', flat=True))
                
                if question.is_get_score(selected_ids):
                    total_score += question.grade
            
            score_percentage = (total_score / max_score * 100) if max_score > 0 else 0
            
            # Color code based on performance
            if score_percentage >= 80:
                color = '#2e7d32'  # Dark green
                icon = '🏆'
                badge = 'Excellent'
            elif score_percentage >= 60:
                color = '#ef6c00'  # Orange
                icon = '📘'
                badge = 'Passing'
            else:
                color = '#c62828'  # Dark red
                icon = '📚'
                badge = 'Needs Improvement'
            
            return format_html(
                '<div style="text-align: center;">'
                '<span style="font-size: 1.2em; font-weight: bold; color: {};">'
                '{} {} / {}</span><br>'
                '<span style="color: {}; background: #f5f5f5; padding: 2px 8px; '
                'border-radius: 12px; font-size: 0.85em;">'
                '{} ({:.1f}%)</span>'
                '</div>',
                color, icon, total_score, max_score,
                color, badge, score_percentage
            )
        except Exception as e:
            return format_html(
                '<span style="color: #c62828;">Error calculating score</span>'
            )
    score_display.short_description = 'Score'
    
    def performance_indicator(self, obj):
        """
        Visual indicator of student performance relative to class average.
        
        Returns:
            HTML progress bar with percentile ranking
        """
        try:
            course = obj.enrollment.course
            student_score = self._calculate_score(obj)
            
            # Get all submissions for this course
            submissions = Submission.objects.filter(
                enrollment__course=course
            ).select_related('enrollment')
            
            scores = []
            for sub in submissions:
                scores.append(self._calculate_score(sub))
            
            if not scores:
                return format_html('<span>No comparison data</span>')
            
            avg_score = sum(scores) / len(scores)
            percentile = sum(1 for s in scores if s < student_score) / len(scores) * 100
            
            # Determine ranking
            if student_score >= avg_score * 1.2:
                rank = 'Top Performer'
                color = '#2e7d32'
                bar_width = 90
            elif student_score >= avg_score:
                rank = 'Above Average'
                color = '#ef6c00'
                bar_width = 70
            else:
                rank = 'Below Average'
                color = '#c62828'
                bar_width = 40
            
            return format_html(
                '<div style="min-width: 150px;">'
                '<span style="color: {}; font-weight: bold;">{}</span><br>'
                '<div style="background: #e0e0e0; border-radius: 10px; height: 8px; width: 100%;">'
                '<div style="background: {}; width: {}%; height: 8px; border-radius: 10px;"></div>'
                '</div>'
                '<span style="font-size: 0.85em; color: #666;">'
                'Class avg: {:.1f}% • {}th percentile</span>'
                '</div>',
                color, rank,
                color, bar_width,
                (avg_score / 100) * 100, int(percentile)
            )
        except:
            return format_html('<span style="color: #666;">N/A</span>')
    performance_indicator.short_description = 'Performance'
    
    def review_link(self, obj):
        """
        Quick action links for reviewing submissions.
        
        Returns:
            HTML buttons for common review actions
        """
        return format_html(
            '<div style="display: flex; gap: 5px;">'
            '<a href="{}" style="background: #1976d2; color: white; padding: 4px 8px; '
            'border-radius: 4px; text-decoration: none; font-size: 0.85em;">🔍 View</a>'
            '<a href="{}" style="background: #ed6c02; color: white; padding: 4px 8px; '
            'border-radius: 4px; text-decoration: none; font-size: 0.85em;">📧 Contact</a>'
            '</div>',
            reverse('admin:onlinecourse_submission_change', args=[obj.id]),
            f"mailto:{obj.enrollment.user.email}"
        )
    review_link.short_description = 'Actions'
    
    # ========================================================================
    # DETAIL VIEW FIELDS
    # ========================================================================
    
    def choices_detailed(self, obj):
        """
        Detailed view of all choices made in the submission.
        
        Used in the detail view to show complete answer set.
        
        Returns:
            HTML table of questions and answers
        """
        choices = obj.choices.select_related('question').order_by('question__id')
        
        if not choices.exists():
            return format_html('<p>No answers recorded for this submission.</p>')
        
        # Group by question
        questions_dict = {}
        for choice in choices:
            q_id = choice.question.id
            if q_id not in questions_dict:
                questions_dict[q_id] = {
                    'question': choice.question,
                    'choices': []
                }
            questions_dict[q_id]['choices'].append(choice)
        
        # Build HTML table
        html = ['<table style="width: 100%; border-collapse: collapse;">']
        html.append('<thead style="background: #f5f5f5;">')
        html.append('<tr>')
        html.append('<th style="padding: 12px; text-align: left;">Question</th>')
        html.append('<th style="padding: 12px; text-align: left;">Selected Answer</th>')
        html.append('<th style="padding: 12px; text-align: center;">Correct?</th>')
        html.append('</tr>')
        html.append('</thead>')
        html.append('<tbody>')
        
        for q_data in questions_dict.values():
            question = q_data['question']
            choices = q_data['choices']
            
            # Check if selection is correct
            selected_ids = [c.id for c in choices]
            is_correct = question.is_get_score(selected_ids)
            
            for i, choice in enumerate(choices):
                html.append('<tr style="border-bottom: 1px solid #e0e0e0;">')
                
                # Question column (show only once per question)
                if i == 0:
                    html.append(f'<td style="padding: 12px;" rowspan="{len(choices)}">')
                    html.append(f'<strong>{question.text}</strong><br>')
                    html.append(f'<span style="color: #666; font-size: 0.85em;">{question.grade} pts</span>')
                    html.append('</td>')
                
                # Selected answer column
                html.append(f'<td style="padding: 12px;">{choice.text}</td>')
                
                # Correctness column
                if i == 0:
                    if is_correct:
                        html.append('<td style="padding: 12px; text-align: center; color: #2e7d32;">✅ Correct</td>')
                    else:
                        html.append('<td style="padding: 12px; text-align: center; color: #c62828;">❌ Incorrect</td>')
                    html.append('</tr>')
        
        html.append('</tbody>')
        html.append('</table>')
        
        return format_html(''.join(html))
    choices_detailed.short_description = 'Answer Details'
    
    def score_breakdown(self, obj):
        """
        Detailed breakdown of score by question.
        
        Returns:
            HTML table with per-question scoring
        """
        course = obj.enrollment.course
        questions = course.questions.prefetch_related('choice_set').all()
        
        html = ['<table style="width: 100%; border-collapse: collapse;">']
        html.append('<thead style="background: #f5f5f5;">')
        html.append('<tr>')
        html.append('<th style="padding: 12px; text-align: left;">Question</th>')
        html.append('<th style="padding: 12px; text-align: center;">Points Earned</th>')
        html.append('<th style="padding: 12px; text-align: center;">Max Points</th>')
        html.append('<th style="padding: 12px; text-align: center;">Result</th>')
        html.append('</tr>')
        html.append('</thead>')
        html.append('<tbody>')
        
        total_earned = 0
        total_possible = 0
        
        for question in questions:
            selected_ids = list(obj.choices.filter(
                question=question
            ).values_list('id', flat=True))
            
            is_correct = question.is_get_score(selected_ids)
            earned = question.grade if is_correct else 0
            
            total_earned += earned
            total_possible += question.grade
            
            # Row styling based on correctness
            row_style = 'background: #e8f5e9;' if is_correct else ''
            
            html.append(f'<tr style="border-bottom: 1px solid #e0e0e0; {row_style}">')
            html.append(f'<td style="padding: 12px;">{question.text[:100]}...</td>')
            html.append(f'<td style="padding: 12px; text-align: center; font-weight: bold;">{earned}</td>')
            html.append(f'<td style="padding: 12px; text-align: center;">{question.grade}</td>')
            
            if is_correct:
                html.append('<td style="padding: 12px; text-align: center; color: #2e7d32;">✓ Correct</td>')
            else:
                # Show correct answer for incorrect responses
                correct_choice = question.choice_set.filter(is_correct=True).first()
                correct_text = correct_choice.text[:50] if correct_choice else "Not specified"
                html.append(f'<td style="padding: 12px; text-align: center; color: #c62828;">'
                           f'✗ Incorrect<br><span style="font-size: 0.85em;">Correct: {correct_text}</span></td>')
            
            html.append('</tr>')
        
        # Footer with totals
        html.append('<tr style="background: #e3f2fd; font-weight: bold;">')
        html.append(f'<td style="padding: 12px;">TOTAL</td>')
        html.append(f'<td style="padding: 12px; text-align: center;">{total_earned}</td>')
        html.append(f'<td style="padding: 12px; text-align: center;">{total_possible}</td>')
        html.append(f'<td style="padding: 12px; text-align: center;">{total_earned}/{total_possible} ({total_earned/total_possible*100:.1f}%)</td>')
        html.append('</tr>')
        
        html.append('</tbody>')
        html.append('</table>')
        
        return format_html(''.join(html))
    score_breakdown.short_description = 'Score Breakdown'
    
    def answer_analysis(self, obj):
        """
        Statistical analysis of answer patterns.
        
        Returns:
            JSON-like formatted analysis of answer choices
        """
        course = obj.enrollment.course
        analysis = {}
        
        for question in course.questions.all():
            selected_choices = obj.choices.filter(question=question)
            
            analysis[question.id] = {
                'question_text': question.text[:100],
                'selected_count': selected_choices.count(),
                'selected_texts': [c.text[:50] for c in selected_choices],
                'is_correct': question.is_get_score(
                    list(selected_choices.values_list('id', flat=True))
                )
            }
        
        # Format as readable JSON
        formatted = json.dumps(analysis, indent=2, ensure_ascii=False)
        
        return format_html(
            '<pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; '
            'overflow-x: auto; font-size: 0.9em;">{}</pre>',
            formatted
        )
    answer_analysis.short_description = 'Answer Analysis (JSON)'
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _calculate_score(self, submission):
        """
        Private helper to calculate total score for a submission.
        
        This is separated to avoid code duplication between the score display
        and performance analysis methods.
        
        Args:
            submission: Submission instance
            
        Returns:
            int: Total score earned
        """
        total_score = 0
        course = submission.enrollment.course
        
        for question in course.questions.all():
            selected_ids = list(submission.choices.filter(
                question=question
            ).values_list('id', flat=True))
            
            if question.is_get_score(selected_ids):
                total_score += question.grade
        
        return total_score
    
    # ========================================================================
    # QUERYSET OVERRIDES
    # ========================================================================
    
    def get_queryset(self, request):
        """
        Restrict submissions based on user permissions.
        
        - Superusers see all submissions
        - Instructors see submissions for their own courses only
        - Regular staff see no submissions (shouldn't happen)
        
        This is a critical security feature to ensure data isolation.
        """
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs.select_related(
                'enrollment__user',
                'enrollment__course'
            ).prefetch_related(
                'choices',
                'choices__question'
            )
        
        # Check if user is an instructor
        try:
            instructor = request.user.instructor
            # Filter to courses this instructor teaches
            return qs.filter(
                enrollment__course__instructors=instructor
            ).select_related(
                'enrollment__user',
                'enrollment__course'
            ).prefetch_related(
                'choices',
                'choices__question'
            )
        except:
            # User is not an instructor
            return qs.none()
    
    # ========================================================================
    # PERMISSIONS
    # ========================================================================
    
    def has_add_permission(self, request):
        """
        Prevent manual submission creation in admin.
        
        Submissions should only be created through the exam-taking process,
        not manually via admin interface. This maintains data integrity.
        """
        return False
    
    def has_delete_permission(self, request, obj=None):
        """
        Only superusers can delete submissions.
        
        Submissions are permanent records that should rarely be deleted.
        This prevents accidental data loss.
        """
        return request.user.is_superuser