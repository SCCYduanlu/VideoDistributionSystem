from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import Project, Member, Video, ExtractionCode, AccessLog

def is_admin(user):
    return user.is_staff

def admin_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('custom_admin:dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'distribution/admin/login.html', {'form': form})

@login_required(login_url='custom_admin:login')
def admin_logout(request):
    logout(request)
    return redirect('custom_admin:login')

@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def dashboard(request):
    projects_count = Project.objects.count()
    members_count = Member.objects.count()
    videos_count = Video.objects.count()
    recent_logs = AccessLog.objects.order_by('-accessed_at')[:10]
    return render(request, 'distribution/admin/dashboard.html', {
        'projects_count': projects_count,
        'members_count': members_count,
        'videos_count': videos_count,
        'recent_logs': recent_logs,
    })

# Project views
@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def project_list(request):
    projects = Project.objects.all().order_by('-created_at')
    return render(request, 'distribution/admin/project_list.html', {'projects': projects})

@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def project_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        if title:
            Project.objects.create(title=title, description=description)
            messages.success(request, '项目创建成功！')
            return redirect('custom_admin:project_list')
    return render(request, 'distribution/admin/project_form.html')

@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    videos = project.videos.all()
    extraction_codes = project.extraction_codes.all()
    return render(request, 'distribution/admin/project_detail.html', {
        'project': project,
        'videos': videos,
        'extraction_codes': extraction_codes,
    })

@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def project_delete(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        project.delete()
        messages.success(request, '项目删除成功！')
        return redirect('custom_admin:project_list')
    return render(request, 'distribution/admin/confirm_delete.html', {'object': project, 'cancel_url': '/admin/projects/'})

# Video views
@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def video_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        title = request.POST.get('title')
        video_file = request.FILES.get('video_file')
        if title and video_file:
            Video.objects.create(project=project, title=title, video_file=video_file)
            messages.success(request, '视频上传成功！')
            return redirect('custom_admin:project_detail', project_id=project.id)
    return render(request, 'distribution/admin/video_form.html', {'project': project})

@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def video_delete(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    project_id = video.project.id
    if request.method == 'POST':
        video.delete()
        messages.success(request, '视频删除成功！')
        return redirect('custom_admin:project_detail', project_id=project_id)
    return render(request, 'distribution/admin/confirm_delete.html', {'object': video, 'cancel_url': f'/admin/projects/{project_id}/'})

# Member / Extraction Code views
@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def add_member_to_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        qq = request.POST.get('qq')
        nickname = request.POST.get('nickname')
        
        if qq and nickname:
            member, created = Member.objects.get_or_create(qq=qq, defaults={'nickname': nickname})
            if not created and member.nickname != nickname:
                member.nickname = nickname
                member.save()
            
            # Generate extraction code
            code, created = ExtractionCode.objects.get_or_create(project=project, member=member)
            if created:
                messages.success(request, f'成功为会员 {nickname} 生成提取码: {code.code}')
            else:
                messages.info(request, f'会员 {nickname} 的提取码已存在: {code.code}')
            
            return redirect('custom_admin:project_detail', project_id=project.id)
            
    return render(request, 'distribution/admin/member_form.html', {'project': project})

@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def code_delete(request, code_id):
    code = get_object_or_404(ExtractionCode, id=code_id)
    project_id = code.project.id
    if request.method == 'POST':
        code.delete()
        messages.success(request, '提取码删除成功！')
        return redirect('custom_admin:project_detail', project_id=project_id)
    return render(request, 'distribution/admin/confirm_delete.html', {'object': code, 'cancel_url': f'/admin/projects/{project_id}/'})
