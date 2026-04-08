from django.urls import path
from . import views

urlpatterns =[
    # Auth & Routing
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.traffic_cop, name='home'),
    path('set-school-year/', views.set_school_year, name='set_school_year'),

    # Staff & Admin Maintenance
    path('maintenance/', views.maintenance_dashboard, name='maintenance_dashboard'),
    path('maintenance/staff/', views.manage_staff, name='manage_staff'),
    path('maintenance/students/', views.manage_students, name='manage_students'),
    path('maintenance/sections/', views.manage_sections, name='manage_sections'),

    # Staff (XP UI)
    path('staff/home/', views.staff_home, name='staff_home'),
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/discipline/<str:category>/', views.disciplinary_module, name='disciplinary_module'),
    path('staff/attendance-review/', views.staff_attendance_review, name='staff_attendance_review'),

    # Portals
    path('beadle/dashboard/', views.beadle_dashboard, name='beadle_dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
]