from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from functools import wraps


def admin_required(view_func):
    """
    Decorator to ensure only admin users can access a view.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_superuser:
            messages.error(request, "Access denied. Admin privileges required.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def supervisor_required(view_func):
    """
    Decorator to ensure only supervisor users can access a view.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_staff or request.user.is_superuser:
            messages.error(request, "Access denied. Supervisor privileges required.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def student_required(view_func):
    """
    Decorator to ensure only student users can access a view.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_staff or request.user.is_superuser:
            messages.error(request, "Access denied. Student access only.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def role_based_redirect(view_func):
    """
    Decorator to redirect users to appropriate dashboard based on their role.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return redirect('admin_dashboard')
            elif request.user.is_staff:
                return redirect('supervisor_dashboard')
            else:
                return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
