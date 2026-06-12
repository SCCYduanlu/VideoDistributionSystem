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
def admin_profile(request):
    from django.contrib.auth import update_session_auth_hash
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    user = request.user
    password_form = PasswordChangeForm(user)
    
    # Add Tailwind classes to form fields manually
    for field in password_form.fields.values():
        field.widget.attrs['class'] = 'shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border'
    
    if request.method == 'POST':
        if 'update_username' in request.POST:
            new_username = request.POST.get('username')
            if new_username and new_username != user.username:
                if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                    messages.error(request, '该用户名已存在，请换一个。')
                else:
                    user.username = new_username
                    user.save()
                    messages.success(request, '用户名修改成功！')
                    return redirect('custom_admin:admin_profile')
                    
        elif 'update_password' in request.POST:
            password_form = PasswordChangeForm(user, request.POST)
            for field in password_form.fields.values():
                field.widget.attrs['class'] = 'shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border'
            
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # 保持登录状态
                messages.success(request, '密码修改成功！')
                return redirect('custom_admin:admin_profile')
            else:
                messages.error(request, '密码修改失败，请检查输入。')
                
    return render(request, 'distribution/admin/admin_profile.html', {
        'password_form': password_form
    })

@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def dashboard(request):
    projects_count = Project.objects.count()
    members_count = Member.objects.count()
    videos_count = Video.objects.count()
    recent_logs = AccessLog.objects.select_related('extraction_code__member', 'extraction_code__project').order_by('-accessed_at')[:20]
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
        code_expire_days = request.POST.get('code_expire_days', 0)
        try:
            code_expire_days = int(code_expire_days)
        except ValueError:
            code_expire_days = 0
            
        if title:
            Project.objects.create(title=title, description=description, code_expire_days=code_expire_days)
            messages.success(request, '项目创建成功！')
            return redirect('custom_admin:project_list')
    return render(request, 'distribution/admin/project_form.html')

@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def project_edit(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        code_expire_days = request.POST.get('code_expire_days', 0)
        update_existing = request.POST.get('update_existing_codes') == 'on'
        
        try:
            code_expire_days = int(code_expire_days)
        except ValueError:
            code_expire_days = 0
            
        if title:
            project.title = title
            project.description = description
            project.code_expire_days = code_expire_days
            project.save()
            
            if update_existing:
                from django.utils import timezone
                import datetime
                codes = project.extraction_codes.all()
                for code in codes:
                    if code_expire_days > 0:
                        code.expires_at = code.created_at + datetime.timedelta(days=code_expire_days)
                    else:
                        code.expires_at = None
                    code.save()
                messages.success(request, f'项目修改成功，并已更新所有 {codes.count()} 个历史提取码的过期时间！')
            else:
                messages.success(request, '项目修改成功！')
                
            return redirect('custom_admin:project_detail', project_id=project.id)
    return render(request, 'distribution/admin/project_form.html', {'project': project})

@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def project_detail(request, project_id):
    from django.db.models import Count, Max
    project = get_object_or_404(Project, id=project_id)
    videos = project.videos.all()
    extraction_codes = project.extraction_codes.select_related('member').annotate(
        access_count=Count('logs'),
        last_access=Max('logs__accessed_at')
    )
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
    return render(request, 'distribution/admin/video_form.html', {'project': project})

import hashlib
import shutil
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def video_upload_status(request, project_id):
    upload_id = request.GET.get('upload_id')
    if not upload_id:
        return JsonResponse({'error': 'Missing upload_id'}, status=400)
    
    safe_id = hashlib.md5(upload_id.encode('utf-8')).hexdigest()
    temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_uploads', safe_id)
    
    uploaded_chunks = []
    if os.path.exists(temp_dir):
        for f in os.listdir(temp_dir):
            if f.startswith('chunk_'):
                try:
                    uploaded_chunks.append(int(f.split('_')[1]))
                except ValueError:
                    pass
    
    return JsonResponse({'uploaded_chunks': uploaded_chunks})

@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def video_upload_chunk(request, project_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    upload_id = request.POST.get('upload_id')
    chunk_index = request.POST.get('chunk_index')
    chunk_file = request.FILES.get('file')
    
    if not all([upload_id, chunk_index, chunk_file]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)
        
    safe_id = hashlib.md5(upload_id.encode('utf-8')).hexdigest()
    temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_uploads', safe_id)
    os.makedirs(temp_dir, exist_ok=True)
    
    chunk_path = os.path.join(temp_dir, f'chunk_{chunk_index}')
    with open(chunk_path, 'wb+') as f:
        for chunk in chunk_file.chunks():
            f.write(chunk)
            
    return JsonResponse({'status': 'ok'})

@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def video_upload_complete(request, project_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    project = get_object_or_404(Project, id=project_id)
    upload_id = request.POST.get('upload_id')
    filename = request.POST.get('filename')
    title = request.POST.get('title')
    total_chunks = request.POST.get('total_chunks')
    
    if not all([upload_id, filename, title, total_chunks]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)
        
    try:
        total_chunks = int(total_chunks)
    except ValueError:
        return JsonResponse({'error': 'Invalid total_chunks'}, status=400)
        
    safe_id = hashlib.md5(upload_id.encode('utf-8')).hexdigest()
    temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_uploads', safe_id)
    
    # Verify all chunks exist
    for i in range(total_chunks):
        if not os.path.exists(os.path.join(temp_dir, f'chunk_{i}')):
            return JsonResponse({'error': f'Missing chunk {i}'}, status=400)
            
    # Merge chunks
    merged_filename = f"{safe_id}_{filename}"
    merged_path = os.path.join(settings.MEDIA_ROOT, 'temp_uploads', merged_filename)
    
    try:
        with open(merged_path, 'wb+') as dest_file:
            for i in range(total_chunks):
                chunk_path = os.path.join(temp_dir, f'chunk_{i}')
                with open(chunk_path, 'rb') as c:
                    shutil.copyfileobj(c, dest_file)
                    
        # Save to Video model
        import random
        from django.core.files import File
        from .utils import get_video_duration
        
        with open(merged_path, 'rb') as f:
            video = Video.objects.create(project=project, title=title)
            video.video_file.save(filename, File(f))
            
        # Generate watermark timestamps
        duration = get_video_duration(video.video_file.path)
        timestamps = []
        if duration > 10:
            for _ in range(3):
                timestamps.append(random.randint(5, int(duration) - 5))
            timestamps.sort()
        else:
            timestamps = [0]
            
        video.watermark_timestamps = timestamps
        video.save()
        
        messages.success(request, '视频上传成功！')
        return JsonResponse({'status': 'ok'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        # Cleanup
        if os.path.exists(merged_path):
            os.remove(merged_path)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

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
            from django.utils import timezone
            import datetime
            
            code, created = ExtractionCode.objects.get_or_create(project=project, member=member)
            if created:
                if project.code_expire_days > 0:
                    code.expires_at = timezone.now() + datetime.timedelta(days=project.code_expire_days)
                    code.save()
                messages.success(request, f'成功为会员 {nickname} 生成提取码: {code.code}')
            else:
                messages.info(request, f'会员 {nickname} 的提取码已存在: {code.code}')
            
            return redirect('custom_admin:project_detail', project_id=project.id)
            
    return render(request, 'distribution/admin/member_form.html', {'project': project})

@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def code_logs(request, code_id):
    code = get_object_or_404(ExtractionCode.objects.select_related('member', 'project'), id=code_id)
    logs = code.logs.all().order_by('-accessed_at')
    return render(request, 'distribution/admin/code_logs.html', {'code': code, 'logs': logs})

@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def code_edit(request, code_id):
    code = get_object_or_404(ExtractionCode, id=code_id)
    if request.method == 'POST':
        expires_at_str = request.POST.get('expires_at')
        if expires_at_str:
            from django.utils.dateparse import parse_datetime
            from django.utils import timezone
            try:
                dt = parse_datetime(expires_at_str)
                if dt is not None:
                    if timezone.is_naive(dt):
                        dt = timezone.make_aware(dt)
                    code.expires_at = dt
            except Exception:
                pass
        else:
            code.expires_at = None
        code.save()
        messages.success(request, f'提取码 {code.code} 的有效期已更新！')
        return redirect('custom_admin:project_detail', project_id=code.project.id)
        
    expires_at_formatted = ''
    if code.expires_at:
        from django.utils import timezone
        local_dt = timezone.localtime(code.expires_at)
        expires_at_formatted = local_dt.strftime('%Y-%m-%dT%H:%M')
        
    return render(request, 'distribution/admin/code_form.html', {
        'code': code,
        'expires_at_formatted': expires_at_formatted
    })

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

@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def watermark_tool(request):
    from .utils import decrypt_token, extract_audio_watermark
    import os
    from django.conf import settings
    
    result = None
    if request.method == 'POST':
        # Check if a file was uploaded for audio extraction
        if 'video_file' in request.FILES:
            uploaded_file = request.FILES['video_file']
            # Save temp file
            temp_path = os.path.join(settings.MEDIA_ROOT, 'temp_upload.mp4')
            with open(temp_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
                    
            try:
                import subprocess
                # Extract audio
                temp_audio = os.path.join(settings.MEDIA_ROOT, 'temp_extract.wav')
                subprocess.run(['ffmpeg', '-y', '-i', temp_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', temp_audio], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Extract token
                token = extract_audio_watermark(temp_audio, token_length=120)
                
                # Cleanup
                if os.path.exists(temp_path): os.remove(temp_path)
                if os.path.exists(temp_audio): os.remove(temp_audio)
                
                if token:
                    request.POST = request.POST.copy()
                    request.POST['token'] = token
                else:
                    result = {'success': False, 'error': '未能在视频音频中检测到有效的水印Token'}
            except Exception as e:
                result = {'success': False, 'error': f'处理视频文件时出错: {str(e)}'}
                
        token = request.POST.get('token')
        if token and not result:
            token = token.strip()
            ext_id, vid_id = decrypt_token(token)
            if ext_id and vid_id:
                try:
                    code = ExtractionCode.objects.get(id=ext_id)
                    video = Video.objects.get(id=vid_id)
                    result = {
                        'success': True,
                        'member': code.member,
                        'project': code.project,
                        'code': code.code,
                        'video': video,
                        'extracted_token': token
                    }
                except (ExtractionCode.DoesNotExist, Video.DoesNotExist):
                    result = {'success': False, 'error': 'Token解析成功，但对应数据已删除'}
            else:
                result = {'success': False, 'error': f'解密失败。提取到的Token为: {token}'}
    return render(request, 'distribution/admin/watermark_tool.html', {'result': result})

import os
import shutil
from django.conf import settings
from .models import WatermarkedVideo, SystemSetting

# Helper function to get directory size
def get_dir_size(path):
    total_size = 0
    if os.path.exists(path):
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
    return total_size

def format_size(size_in_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0

@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def storage_monitor(request):
    media_root = settings.MEDIA_ROOT
    original_videos_path = os.path.join(media_root, 'videos')
    watermarked_cache_path = os.path.join(media_root, 'watermarked')
    
    # Calculate sizes
    original_size = get_dir_size(original_videos_path)
    cache_size = get_dir_size(watermarked_cache_path)
    total_media_size = get_dir_size(media_root)
    other_size = total_media_size - original_size - cache_size
    if other_size < 0: other_size = 0
    
    # Disk usage (windows)
    total, used, free = shutil.disk_usage(media_root)
    
    # Count files
    watermarked_count = WatermarkedVideo.objects.filter(status='done').count()
    original_count = Video.objects.count()
    
    # Handle clear cache action
    if request.method == 'POST' and request.POST.get('action') == 'clear_cache':
        # 1. Delete physical files
        if os.path.exists(watermarked_cache_path):
            for item in os.listdir(watermarked_cache_path):
                item_path = os.path.join(watermarked_cache_path, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
        
        # 2. Re-create the empty directory
        os.makedirs(watermarked_cache_path, exist_ok=True)
        
        # 3. Update database status
        WatermarkedVideo.objects.all().delete()
        
        messages.success(request, '已成功清理所有防盗水印视频缓存！空间已释放。')
        return redirect('custom_admin:storage_monitor')

    context = {
        'original_size_raw': original_size,
        'cache_size_raw': cache_size,
        'other_size_raw': other_size,
        'total_media_size_raw': total_media_size,
        
        'original_size': format_size(original_size),
        'cache_size': format_size(cache_size),
        'other_size': format_size(other_size),
        'total_media_size': format_size(total_media_size),
        
        'disk_total': format_size(total),
        'disk_used': format_size(used),
        'disk_free': format_size(free),
        'disk_percent': round((used / total) * 100, 1) if total > 0 else 0,
        
        'watermarked_count': watermarked_count,
        'original_count': original_count,
    }
    return render(request, 'distribution/admin/storage_monitor.html', context)

@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def system_settings(request):
    setting = SystemSetting.get_setting()
    
    if request.method == 'POST':
        site_title = request.POST.get('site_title')
        if site_title:
            setting.site_title = site_title
            
        bg_opacity = request.POST.get('bg_opacity')
        if bg_opacity is not None and bg_opacity != '':
            try:
                setting.bg_opacity = int(bg_opacity)
            except ValueError:
                pass
                
        if 'bg_image' in request.FILES:
            # Delete old image if exists
            if setting.bg_image:
                if os.path.exists(setting.bg_image.path):
                    os.remove(setting.bg_image.path)
            setting.bg_image = request.FILES['bg_image']
        elif 'clear_bg' in request.POST:
            if setting.bg_image:
                if os.path.exists(setting.bg_image.path):
                    os.remove(setting.bg_image.path)
            setting.bg_image = None
            
        setting.save()
        messages.success(request, '系统设置已成功保存！')
        return redirect('custom_admin:system_settings')
        
    return render(request, 'distribution/admin/settings.html', {'setting': setting})
