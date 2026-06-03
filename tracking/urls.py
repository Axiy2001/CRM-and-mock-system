from django.urls import path
from . import views

urlpatterns = [
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/take/', views.take_attendance, name='take_attendance'),
    path('homeworks/', views.homework_list, name='homework_list'),
    path('homeworks/check/', views.check_homework, name='check_homework'),
    path('homeworks/create/', views.create_homework, name='create_homework'),
    path('homeworks/<int:homework_id>/', views.homework_detail, name='homework_detail'),

]