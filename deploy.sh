#!/bin/bash

# 打印带颜色的提示信息
echo -e "\033[34m====================================================\033[0m"
echo -e "\033[34m      视频分发系统 - 自动化部署与初始化脚本       \033[0m"
echo -e "\033[34m====================================================\033[0m"

# 1. 自动获取本机公网 IP 并生成 .env 文件
echo -e "\n\033[33m[1/5] 正在检测服务器公网 IP...\033[0m"
PUBLIC_IP=$(curl -s ifconfig.me)

if [ -z "$PUBLIC_IP" ]; then
    echo -e "\033[31m无法自动获取公网 IP，将使用本地默认配置。\033[0m"
    PUBLIC_IP="localhost"
else
    echo -e "\033[32m检测到公网 IP: $PUBLIC_IP\033[0m"
fi

# 写入 .env 文件
echo "TRUSTED_ORIGINS=http://${PUBLIC_IP}:8000,http://${PUBLIC_IP},http://localhost:8000" > .env
echo -e "\033[32m已生成 .env 配置文件，自动配置 CSRF 信任名单。\033[0m"

# 2. 配置 Docker 国内镜像加速 (防止拉取 python 镜像超时)
echo -e "\n\033[33m[2/5] 正在配置 Docker 国内镜像加速...\033[0m"
mkdir -p /etc/docker
cat <<EOF > /etc/docker/daemon.json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.nju.edu.cn",
    "https://dockerproxy.com"
  ]
}
EOF
systemctl daemon-reload
systemctl restart docker
echo -e "\033[32mDocker 镜像加速配置完成并已重启服务。\033[0m"

# 3. 启动 Docker 容器
echo -e "\n\033[33m[3/5] 正在构建并启动 Docker 容器...\033[0m"
docker-compose up -d --build

if [ $? -ne 0 ]; then
    echo -e "\033[31mDocker 启动失败，请检查是否已安装 docker 和 docker-compose。\033[0m"
    exit 1
fi

# 4. 等待数据库准备并执行迁移
echo -e "\n\033[33m[4/5] 正在初始化数据库和静态文件...\033[0m"
sleep 5 # 等待容器完全启动
docker exec video_distribution_web python manage.py migrate
docker exec video_distribution_web python manage.py collectstatic --noinput

# 5. 创建超级管理员
echo -e "\n\033[33m[5/5] 正在创建初始超级管理员...\033[0m"
echo -e "正在使用默认配置创建账号: \033[32madmin\033[0m / 密码: \033[32madmin123\033[0m"
docker exec video_distribution_web bash -c "
cat <<EOF | python manage.py shell
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ 默认管理员创建成功！')
else:
    print('⚠️ 管理员 admin 已存在，跳过创建。')
EOF
"

echo -e "\n\033[34m====================================================\033[0m"
echo -e "\033[32m🎉 部署彻底完成！\033[0m"
echo -e "请确保您的云服务器防火墙已放行 \033[33m8000\033[0m 端口。"
echo -e "访问地址: \033[36mhttp://${PUBLIC_IP}:8000/\033[0m"
echo -e "后台地址: \033[36mhttp://${PUBLIC_IP}:8000/admin/login/\033[0m"
echo -e "\033[31m⚠️ 强烈建议：首次登录后，立即点击右上角修改初始密码！\033[0m"
echo -e "\033[34m====================================================\033[0m"