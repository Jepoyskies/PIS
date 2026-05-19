from django.urls import path
from . import views


urlpatterns = [
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
    path('api/student/<str:student_id>/offenses/', views.api_student_offenses, name='api_student_offenses'),
    
    # INJECTED FIX: Added <int:batch_id>
    path('staff/attendance-review/<int:batch_id>/', views.staff_attendance_review, name='staff_attendance_review'),
    

    # Portals
    path('beadle/dashboard/', views.beadle_dashboard, name='beadle_dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),

    #Dashboard Buttons
    path('reports/', views.reports_dashboard, name='reports_dashboard'),

    path('staff/attendance/list/', views.staff_attendance_list, name='staff_attendance_list'),
    path('staff/attendance/review/<int:batch_id>/', views.staff_attendance_review, name='staff_attendance_review'),
    path('staff/attendance/approve/<int:batch_id>/', views.approve_attendance_batch, name='approve_attendance_batch'),
    path('api/offenses/list/', views.api_get_offenses, name='api_get_offenses'),
    path('staff/report/student/<str:student_id>/', views.generate_student_report, name='student_report'),
    path('api/record/<int:record_id>/toggle-served/', views.api_toggle_served, name='api_toggle_served'),
    path('api/record/<int:record_id>/toggle-served/', views.api_toggle_served, name='api_toggle_served'),
    path('reports/student-demerits/', views.report_student_demerits, name='report_student_demerits'),
    path('reports/enrolment-summary/', views.report_enrolment_summary, name='report_enrolment_summary'),
    path('reports/class-list/', views.report_class_list, name='report_class_list'),
    path('reports/birthdays/', views.report_birthdays, name='report_birthdays'),
    path('reports/student-status/', views.report_student_status, name='report_student_status'),
    path('reports/conduct-marks/', views.report_conduct_marks, name='report_conduct_marks'),
    path('reports/student-record/', views.report_student_record, name='report_student_record'),
    path('reports/attendance-registrar/', views.report_attendance_registrar, name='report_attendance_registrar'),
    path('reports/unserved-cs/', views.report_unserved_cs, name='report_unserved_cs'),
    path('reports/student-directory/', views.report_student_directory, name='report_student_directory'),
    path('reports/conduct-graph/', views.report_conduct_graph, name='report_conduct_graph'),
    path('reports/citizenship-nationality/', views.report_citizenship_nationality, name='report_citizenship_nationality'),
]