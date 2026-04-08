from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def admin_required(view_func):
    """Only allows superusers (Admin)"""
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied 
    return wrapper

def staff_required(view_func):
    """Allows Admin and Staff"""
    def wrapper(request, *args, **kwargs):
        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper

def beadle_required(view_func):
    """Allows only the assigned Beadle"""
    def wrapper(request, *args, **kwargs):
        if hasattr(request.user, 'student_profile'):
            student = request.user.student_profile
            # Check if student is marked as beadle or is assigned to a section as a beadle
            if student.is_beadle or student.beadle_of.exists():
                return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper