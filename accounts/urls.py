from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('students/create/', views.create_student, name='create_student'),
    path('students/<int:student_id>/', views.student_profile, name='student_profile'),

    path('mock-creators/create/', views.create_mock_creator, name='create_mock_creator'),
]