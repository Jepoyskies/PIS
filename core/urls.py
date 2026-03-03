from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Main Gatekeeper
    path('', views.home, name='home'),

    # --- RIS MODULE ---
    path('ris/', views.ris_dashboard, name='ris_dashboard'),
    path('ris/sections/', views.ris_sections, name='ris_sections'),

    # --- PIS MODULE ---
    path('pis/', views.pis_home, name='pis_home'),  # The PIS Menu
    path('pis/students/', views.pis_dashboard, name='pis_dashboard'), # The Student Grid
    path('pis/discipline/<str:category>/', views.disciplinary_module, name='disciplinary_module'), 
]