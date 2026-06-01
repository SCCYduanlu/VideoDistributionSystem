from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import ExtractionCode, AccessLog

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
        'member': extraction_code.member
    })