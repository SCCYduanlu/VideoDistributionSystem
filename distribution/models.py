from django.db import models
from django.utils.crypto import get_random_string

class Project(models.Model):
    title = models.CharField(max_length=200, verbose_name='项目名称')
    description = models.TextField(blank=True, verbose_name='项目描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '视频项目'
        verbose_name_plural = '视频项目'

    def __str__(self):
        return self.title

class Member(models.Model):
    qq = models.CharField(max_length=20, unique=True, verbose_name='QQ号')
    nickname = models.CharField(max_length=100, verbose_name='昵称')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='录入时间')

    class Meta:
        verbose_name = '会员'
        verbose_name_plural = '会员'

    def __str__(self):
        return f"{self.nickname} ({self.qq})"

class Video(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='videos', verbose_name='所属项目')
    title = models.CharField(max_length=200, verbose_name='视频标题')
    video_file = models.FileField(upload_to='videos/%Y/%m/', verbose_name='视频文件')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')

    class Meta:
        verbose_name = '视频'
        verbose_name_plural = '视频'

    def __str__(self):
        return self.title

class ExtractionCode(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='extraction_codes', verbose_name='项目')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='extraction_codes', verbose_name='会员')
    code = models.CharField(max_length=20, unique=True, verbose_name='提取码')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='生成时间')
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='过期时间')
    is_active = models.BooleanField(default=True, verbose_name='是否有效')

    class Meta:
        verbose_name = '提取码'
        verbose_name_plural = '提取码'
        unique_together = ('project', 'member')

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = get_random_string(10)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.project.title} - {self.member.nickname} - {self.code}"

class AccessLog(models.Model):
    extraction_code = models.ForeignKey(ExtractionCode, on_delete=models.CASCADE, related_name='logs', verbose_name='提取码')
    ip_address = models.GenericIPAddressField(verbose_name='访问IP')
    user_agent = models.TextField(verbose_name='User Agent')
    accessed_at = models.DateTimeField(auto_now_add=True, verbose_name='访问时间')

    class Meta:
        verbose_name = '访问日志'
        verbose_name_plural = '访问日志'
        ordering = ['-accessed_at']

    def __str__(self):
        return f"{self.extraction_code.code} - {self.ip_address}"
