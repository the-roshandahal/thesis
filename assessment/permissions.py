from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

# Permission Functions (simplified)
def has_assessment_view_permission(user):
    """Check if user can view assessments"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def has_assessment_manage_permission(user):
    """Check if user can manage assessments (create, edit, delete)"""
    return user.is_authenticated and user.is_superuser

# Permission Decorators (only the ones actually used)
def assessment_view_required(view_func):
    """Decorator to check if user can view assessments"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not has_assessment_view_permission(request.user):
            messages.error(request, "Access denied. You don't have permission to view assessments.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def assessment_manage_required(view_func):
    """Decorator to check if user can manage assessments"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not has_assessment_manage_permission(request.user):
            messages.error(request, "Access denied. Admin privileges required to manage assessments.")
            return redirect('assessment_schema')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
