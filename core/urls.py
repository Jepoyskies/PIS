# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('students/', views.dashboard, name='dashboard'),
    
    # ONE route for all legacy disciplinary modules
    path('discipline/<str:category>/', views.disciplinary_module, name='disciplinary_module'), 
]