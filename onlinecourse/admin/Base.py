"""
Base admin classes and utility mixins.
These provide reusable functionality across all admin interfaces.
Following the DRY (Don't Repeat Yourself) principle.
"""
from django.contrib import admin
from django.http import HttpResponse
import csv


class ExportCSVMixin:
    """
    Mixin to add CSV export functionality to any ModelAdmin.
    
    Why a mixin? Because multiple admin classes (Submissions, Enrollments, Users)
    may need CSV export. This keeps the code DRY and maintainable.
    
    Usage:
        class MyAdmin(ExportCSVMixin, admin.ModelAdmin):
            export_fields = ['field1', 'field2']
    """
    
    export_fields = None  # Override in child class
    export_filename = 'export.csv'  # Override in child class
    
    def export_as_csv(self, request, queryset):
        """
        Export selected objects as CSV file.
        
        This is a Django admin action that processes the selected queryset
        and generates a downloadable CSV file.
        
        Args:
            request: HTTP request object
            queryset: Selected objects from admin list view
            
        Returns:
            HttpResponse with CSV attachment
        """
        # Validate that export_fields is defined
        if not self.export_fields:
            self.message_user(
                request, 
                "Please define export_fields in your ModelAdmin",
                level='ERROR'
            )
            return
        
        # Create HTTP response with CSV content type
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{self.export_filename}"'
        
        writer = csv.writer(response)
        writer.writerow(self.export_fields)  # Write headers
        
        # Write data rows
        for obj in queryset:
            row = []
            for field in self.export_fields:
                # Handle dotted field paths (e.g., 'user__username')
                value = obj
                for part in field.split('__'):
                    value = getattr(value, part, '')
                    if callable(value):
                        value = value()
                row.append(str(value)[:100])  # Truncate long values
            writer.writerow(row)
        
        return response
    
    export_as_csv.short_description = "Export selected items as CSV"


class TimestampedAdminMixin:
    """
    Mixin for models with created_at/updated_at timestamps.
    
    Automatically configures readonly fields and list display for
    timestamp fields, ensuring data integrity by preventing manual edits.
    """
    
    def get_readonly_fields(self, request, obj=None):
        """
        Add timestamp fields to readonly fields.
        
        Why? Timestamps should never be manually edited as they represent
        system-generated audit information. This method ensures they're
        always readonly, even if someone forgets to specify it.
        
        Args:
            request: HTTP request object
            obj: Current object being edited (None for add form)
            
        Returns:
            Tuple of readonly field names
        """
        readonly_fields = super().get_readonly_fields(request, obj)
        timestamp_fields = ['created_at', 'updated_at']
        
        # Only add fields that actually exist in the model
        existing_fields = [
            field for field in timestamp_fields 
            if hasattr(self.model, field)
        ]
        
        return tuple(set(readonly_fields + tuple(existing_fields)))