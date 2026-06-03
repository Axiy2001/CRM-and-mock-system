from django.urls import path
from . import views

urlpatterns = [
    path('', views.mock_list, name='mock_list'),
    path('create/', views.create_mock, name='create_mock'),
    path('<int:mock_id>/', views.mock_detail, name='mock_detail'),
    path(
    '<int:mock_id>/delete/',
    views.delete_mock,
    name='delete_mock'
),
]