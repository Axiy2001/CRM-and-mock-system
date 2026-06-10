from django.urls import path
from . import views

urlpatterns = [
    path('', views.assistant_dashboard, name='assistant_dashboard'),
	 path('progress/', views.student_progress_list, name='student_progress_list'),
	 path('payments/', views.payment_crm, name='payment_crm'),
	 path('students/', views.students_crm, name='students_crm'),
	 path('classes/', views.classes_crm, name='classes_crm'),
	 path(
    'teachers/',
    views.teacher_crm,
    name='teacher_crm'
),	
]