# 🎥 主播会员专属视频分发系统

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Django](https://img.shields.io/badge/Django-5.0+-green.svg)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-orange.svg)
![TailwindCSS](https://img.shields.io/badge/Tailwind-CSS-38B2AC.svg)

这是一个专为**内容创作者（主播、UP主、画师等）**量身打造的私域视频分发与防盗版系统。

如果你在 Patreon、爱发电等平台拥有自己的“包月赞助”会员，并且需要将高质量视频分发给他们，同时又极度担心视频被内鬼泄露、盗版和二次倒卖。那么，这个系统就是为你准备的。

## ✨ 核心特性

### 🛡️ 极致的防盗版引擎：无损音频隐写术 (Audio Steganography)
告别传统的“降低画质的硬编码视频水印”，本系统采用业内先进的**音频频域隐写术**。
- **零画质损失**：不触碰视频画面（Video Stream Copy），只提取音轨处理，原画质 100% 保留。
- **高隐蔽性**：将经过 `Fernet` 强加密的用户专属 Token（包含内鬼的 QQ、昵称等身份标识）转换为二进制后，隐藏在音频的 15kHz-20kHz 极高频段。人耳完全无法察觉，且不易引起盗版者的防备。
- **无损音频极速封装**：采用 `ALAC` (Apple Lossless) 无损编码重写音轨，不仅防止了有损压缩导致的水印丢失，还将最终封装时间压缩至数秒内。

### 🕵️‍♂️ 泄露溯源：一键抓内鬼工具
如果你的视频在其他平台被盗版发布，只需将盗版视频下载并上传至本系统的**“水印解析工具”**：
- 系统会自动提取音轨并进行逆向解码。
- 瞬间定位出泄露该视频的具体提取码、会员昵称、QQ号，让内鬼无所遁形。

### 👑 会员订阅与有效期管理
- **灵活的提取码机制**：通过简单的录入，即可为主播生成唯一的 10 位字母数字提取码。
- **包月订阅支持**：支持项目级别和独立提取码级别的**有效期（过期时间）设置**。到期后提取码自动失效，完美契合包月/包年的付费订阅模式。

### 🖥️ 现代化的管理后台与粉丝取件端
- **全定制 UI**：彻底弃用 Django 默认 Admin，采用 Tailwind CSS 打造了流畅、响应式的现代化交互界面。
- **服务器存储监控**：“一人一版”的水印分发机制会占用大量存储。系统自带直观的磁盘空间监控看板，并支持**一键清空防盗缓存**以释放空间，且不影响源文件。
- **品牌自定义**：管理员可在后台随时更改提取端的页面标题、动态背景图以及不透明度，并支持上传图片的**即时本地预览**。

---

## 🛠️ 技术栈

- **后端框架**: Django 5.0.2
- **前端样式**: Tailwind CSS (通过 CDN 引入) + FontAwesome 图标
- **多媒体处理**: 
  - `FFmpeg` (音视频分离与封装)
  - `scipy` & `numpy` (音频 DSP 信号处理与频域 DCT 变换)
- **安全与加密**: `cryptography` (Fernet 对称加密)

---

## 🚀 快速部署指南

> **强烈推荐使用 Docker 进行一键部署**，这将完美解决繁琐的 `FFmpeg` 安装配置与环境依赖问题。

### 方案 A：Docker 一键部署 (推荐 🌟)

1. **确保服务器已安装 Docker 和 Docker Compose**
2. **克隆代码并进入目录**
   ```bash
   git clone <your-repository-url>
   cd VideoDistributionSystem
   ```
3. **一键启动服务**
   ```bash
   docker-compose up -d --build
   ```
4. **初始化数据库并创建管理员**
   ```bash
   # 执行数据库迁移
   docker exec -it video_distribution_web python manage.py migrate
   # 创建超级管理员账号
   docker exec -it video_distribution_web python manage.py createsuperuser
   ```
> 此时服务已在 `http://你的服务器IP:8000` 运行。所有数据和视频文件会自动保存在宿主机的 `db.sqlite3` 和 `media` 目录下，不用担心重启数据丢失。

---

### 方案 B：本地环境手动部署

#### 1. 环境准备
确保你的服务器或本地开发环境已安装：
- **Python 3.10** 或更高版本
- **FFmpeg**（必须安装并将其添加到系统的环境变量 `PATH` 中）

#### 2. 克隆项目与安装依赖
```bash
# 克隆代码
git clone <your-repository-url>
cd VideoDistributionSystem

# 建议使用虚拟环境
python -m venv venv
# Windows 激活
venv\Scripts\activate
# Linux/Mac 激活
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 3. 数据库迁移
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 4. 创建超级管理员
创建一个用于登录后台的管理员账号：
```bash
python manage.py createsuperuser
```

#### 5. 启动服务
```bash
python manage.py runserver
```
- **后台管理系统**: `http://127.0.0.1:8000/admin/login/` (使用你刚创建的超级管理员账号登录)
- **粉丝取件端**: `http://127.0.0.1:8000/`

---

## 📖 核心使用流程

1. **配置外观**：登录后台，进入【系统设置】，上传一张好看的背景图，并设置你的品牌标题。
2. **创建项目**：进入【项目管理】，点击“新建项目”。例如：“2026年6月专属视频”，并可按需设置**提取码有效期**（例如 30 天）。
3. **上传视频**：在项目详情中上传你需要分发的高清视频。
4. **发放提取码**：在项目详情中点击“录入会员”，输入粉丝的 QQ 号和昵称，系统会立刻生成一串专属提取码。将此码发送给该粉丝。
5. **粉丝下载**：粉丝访问网站首页，输入提取码。在点击“生成安全下载”后，服务器会在后台瞬间将该粉丝的专属身份 Token 隐写进音频中，并提供下载链接。

## ⚠️ 注意事项

- **FFmpeg 路径**：如果在生成带水印视频或解析工具中遇到报错，请务必检查 `ffmpeg` 是否能在命令行的任何目录下被直接调用。
- **静音录屏防线**：由于采用的是“音频隐写术”，若盗版者在翻录视频时**彻底关闭了系统声音（静音录屏）**，水印将无法被追踪。在后续的更新中，可考虑结合极低透明度的动态视觉水印作为补充防线。
