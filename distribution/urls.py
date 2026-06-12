from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    path('login/', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),
    path('profile/', views.admin_profile, name='admin_profile'),
    path('', views.dashboard, name='dashboard'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('projects/<int:project_id>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:project_id>/delete/', views.project_delete, name='project_delete'),
    
    path('projects/<int:project_id>/video/add/', views.video_create, name='video_create'),
    path('video/<int:video_id>/delete/', views.video_delete, name='video_delete'),
    
    path('projects/<int:project_id>/member/add/', views.add_member_to_project, name='add_member'),
    path('code/<int:code_id>/logs/', views.code_logs, name='code_logs'),
    path('code/<int:code_id>/edit/', views.code_edit, name='code_edit'),
    path('code/<int:code_id>/delete/', views.code_delete, name='code_delete'),
    
    path('watermark/', views.watermark_tool, name='watermark_tool'),
    path('storage/', views.storage_monitor, name='storage_monitor'),
    path('settings/', views.system_settings, name='system_settings'),
]