from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    path('login/', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('projects/<int:project_id>/delete/', views.project_delete, name='project_delete'),
    
    path('projects/<int:project_id>/video/add/', views.video_create, name='video_create'),
    path('video/<int:video_id>/delete/', views.video_delete, name='video_delete'),
    
    path('projects/<int:project_id>/member/add/', views.add_member_to_project, name='add_member'),
    path('code/<int:code_id>/delete/', views.code_delete, name='code_delete'),
]