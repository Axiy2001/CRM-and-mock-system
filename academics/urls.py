from django.urls import path
from . import views

urlpatterns = [
    path('classes/', views.class_list, name='class_list'),
    path('classes/create/', views.create_class, name='create_class'),
    path('classes/<int:class_id>/assign-teacher/', views.assign_teacher, name='assign_teacher'),
    path('classes/<int:class_id>/manage-students/', views.manage_students, name='manage_students'),
    path('classes/<int:class_id>/assign-assistant-admin/',
    views.assign_assistant_admin,
    name='assign_assistant_admin'),
]