from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

# Permission Functions
def is_supervisor(user):
    """Check if user is a supervisor (staff but not superuser)"""
    return user.is_authenticated and user.is_staff and not user.is_superuser

def is_admin(user):
    """Check if user is an admin (superuser)"""
    return user.is_authenticated and user.is_superuser

def is_student(user):
    """Check if user is a student (not staff, not superuser)"""
    return user.is_authenticated and not user.is_staff and not user.is_superuser

def has_assessment_view_permission(user):
    """Check if user can view assessments"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def has_assessment_manage_permission(user):
    """Check if user can manage assessments (create, edit, delete)"""
    return user.is_authenticated and user.is_superuser

def has_project_manage_permission(user):
    """Check if user can manage projects"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)

# Permission Decorators
def supervisor_required(view_func):
    """Decorator to check if user is supervisor"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not is_supervisor(request.user):
            messages.error(request, "Access denied. Supervisor privileges required.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_required(view_func):
    """Decorator to check if user is admin"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not is_admin(request.user):
            messages.error(request, "Access denied. Admin privileges required.")
            return redirect('assessment_schema')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

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

def supervisor_or_admin_required(view_func):
    """Decorator to check if user is supervisor or admin"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access this page.")
            return redirect('login')
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "Access denied. Supervisor or Admin privileges required.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# Permission Mixins for Class-Based Views
class SupervisorRequiredMixin(UserPassesTestMixin):
    """Mixin to require supervisor privileges"""
    def test_func(self):
        return is_supervisor(self.request.user)
    
    def handle_no_permission(self):
        messages.error(self.request, "Access denied. Supervisor privileges required.")
        return redirect('home')

class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to require admin privileges"""
    def test_func(self):
        return is_admin(self.request.user)
    
    def handle_no_permission(self):
        messages.error(self.request, "Access denied. Admin privileges required.")
        return redirect('assessment_schema')

class AssessmentViewRequiredMixin(UserPassesTestMixin):
    """Mixin to require assessment view permission"""
    def test_func(self):
        return has_assessment_view_permission(self.request.user)
    
    def handle_no_permission(self):
        messages.error(self.request, "Access denied. You don't have permission to view assessments.")
        return redirect('home')

class AssessmentManageRequiredMixin(UserPassesTestMixin):
    """Mixin to require assessment management permission"""
    def test_func(self):
        return has_assessment_manage_permission(self.request.user)
    
    def handle_no_permission(self):
        messages.error(self.request, "Access denied. Admin privileges required to manage assessments.")
        return redirect('assessment_schema')

# Context Processors for Templates
def user_permissions(request):
    """Add user permissions to template context"""
    if request.user.is_authenticated:
        return {
            'user_is_supervisor': is_supervisor(request.user),
            'user_is_admin': is_admin(request.user),
            'user_is_student': is_student(request.user),
            'can_view_assessments': has_assessment_view_permission(request.user),
            'can_manage_assessments': has_assessment_manage_permission(request.user),
            'can_manage_projects': has_project_manage_permission(request.user),
        }
    return {
        'user_is_supervisor': False,
        'user_is_admin': False,
        'user_is_student': False,
        'can_view_assessments': False,
        'can_manage_assessments': False,
        'can_manage_projects': False,
    }
