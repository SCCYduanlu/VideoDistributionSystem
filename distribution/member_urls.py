from django.urls import path
from . import member_views

app_name = 'member'

urlpatterns = [
    path('', member_views.index, name='index'),
    path('verify/', member_views.verify_code, name='verify_code'),
    path('videos/<str:code>/', member_views.video_list, name='video_list'),
]