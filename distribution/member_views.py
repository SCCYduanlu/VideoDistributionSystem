from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from .models import ExtractionCode, AccessLog, WatermarkedVideo, Video
from .utils import start_watermark_task
import os
from django.conf import settings

def index(request):
    return render(request, 'distribution/member/index.html')

def verify_code(request):
    if request.method == 'POST':
        code_str = request.POST.get('code')
        try:
            code = ExtractionCode.objects.get(code=code_str, is_active=True)
            # Log access
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            AccessLog.objects.create(
                extraction_code=code,
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:200]
            )
            return redirect('member:video_list', code=code.code)
        except ExtractionCode.DoesNotExist:
            messages.error(request, '无效的提取码或提取码已过期')
            return redirect('member:index')
    return redirect('member:index')

def video_list(request, code):
    extraction_code = get_object_or_404(ExtractionCode, code=code, is_active=True)
    project = extraction_code.project
    videos = project.videos.all()
    return render(request, 'distribution/member/video_list.html', {
        'project': project,
        'videos': videos,
        'member': extraction_code.member,
        'code': extraction_code.code,
    })

def download_video(request, code, video_id):
    extraction_code = get_object_or_404(ExtractionCode, code=code, is_active=True)
    video = get_object_or_404(Video, id=video_id, project=extraction_code.project)
    
    # Check if a watermarked video already exists
    wv, created = WatermarkedVideo.objects.get_or_create(
        extraction_code=extraction_code,
        video=video,
    )
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # AJAX polling for status
        if wv.status == 'done':
            download_url = f"{settings.MEDIA_URL}{wv.file_path}"
            return JsonResponse({'status': 'done', 'url': download_url})
        elif wv.status == 'failed':
            return JsonResponse({'status': 'failed'})
        else:
            if created or wv.status == 'pending':
                start_watermark_task(wv.id)
                # Need to fetch it again since start_watermark_task runs in a thread 
                # but might update it slightly later, so we just return the current status
            return JsonResponse({'status': wv.status})
            
    # Direct access (fallback or direct download)
    if wv.status == 'done':
        file_full_path = os.path.join(settings.MEDIA_ROOT, wv.file_path)
        if os.path.exists(file_full_path):
            response = FileResponse(open(file_full_path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{video.title}.mp4"'
            return response
            
    # If not done, redirect back to list
    messages.info(request, '视频正在后台添加专属防盗水印，请稍候再试。')
    return redirect('member:video_list', code=code)