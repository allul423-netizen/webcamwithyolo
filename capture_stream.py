import cv2
import sys
import time

# 优先使用 yt-dlp（支持cookies，推荐）
try:
    import yt_dlp
    USE_YTDLP = True
    BACKEND = 'ytdlp'
    print("[INFO] 使用 yt-dlp 作为视频解析引擎（支持cookies）")
except ImportError:
    # 备用方案 streamlink
    try:
        import streamlink
        USE_YTDLP = False
        USE_STREAMLINK = True
        print("[WARN] yt-dlp 未安装，使用 streamlink 作为备用")
    except ImportError:
        # 备用方案 pytube
        try:
            from pytube import YouTube
            USE_YTDLP = False
            USE_STREAMLINK = False
            BACKEND = 'pytube'
            print("[WARN] yt-dlp 和 streamlink 未安装，使用 pytube 作为备用")
        except ImportError:
            print("[ERROR] 未安装任何视频解析库")
            print("推荐安装: pip install yt-dlp")
            sys.exit(1)

# 新宿地区直播链接列表（按优先级排序）
# 注意：YouTube直播需要登录/特殊权限，建议使用本地视频测试
SHINJUKU_STREAM_URLS = [
    "https://www.youtube.com/watch?v=gFRtAAmiFbE",   # 测试链接（无需登录）
    "https://www.youtube.com/watch?v=6--o9JRwy3c",   # 新宿大路口（YouTube）- 需要登录
    "https://www.youtube.com/watch?v=gxG3btrRlT8",   # 新宿アルタ前（YouTube）- 需要登录
]

def test_stream_url(url, max_retries=3):
    """
    测试视频流是否可用
    """
    # 本地文件总是视为可用
    if url.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        return True
        
    for attempt in range(max_retries):
        try:
            stream_url = get_stream_url(url)
            if stream_url:
                cap = cv2.VideoCapture(stream_url)
                if cap.isOpened():
                    cap.release()
                    return True
        except Exception as e:
            print(f"  测试失败 (尝试 {attempt + 1}/{max_retries}): {e}")
        
        if attempt < max_retries - 1:
            time.sleep(1)
    
    return False

def get_stream_url_streamlink(url):
    """
    使用 streamlink 获取流地址（推荐用于直播）
    """
    try:
        session = streamlink.Streamlink()
        # 解析所有可用流 - 使用 session.streams() 而不是 resolve_url_no_redirect
        streams = session.streams(url)
        
        if streams and len(streams) > 0:
            # 获取最佳质量流（直播流）
            stream = streams.get('best')
            if stream:
                return stream.url
            # 如果没有'best'，尝试其他常见流名称
            for quality in ['1080p', '720p', '480p', '360p']:
                if quality in streams:
                    return streams[quality].url
            # 如果都没有，尝试取第一个可用流
            first_stream_key = list(streams.keys())[0]
            return streams[first_stream_key].url
        
        print("[ERROR] streamlink: 未找到可用的视频流")
        return None
    except Exception as e:
        print(f"[ERROR] streamlink 获取视频流失败: {e}")
        return None

def get_stream_url_pytube(url):
    """
    使用 pytube 获取 YouTube 视频流地址
    """
    try:
        yt = YouTube(url)
        # 获取最佳视频流（优先选择 720p）
        stream = yt.streams.filter(file_extension='mp4', progressive=True).first()
        if not stream:
            stream = yt.streams.filter(file_extension='mp4').first()
        
        if stream:
            return stream.url
        else:
            print("[ERROR] pytube: 未找到可用的视频流")
            return None
    except Exception as e:
        print(f"[ERROR] pytube 获取视频流失败: {e}")
        return None

def get_stream_url_ytdlp(url, use_cookies=False):
    """
    使用 yt-dlp 获取 YouTube 视频流地址
    """
    ydl_opts = {
        'format': 'best[height<=720]',  # 选择 720p 或更低分辨率
        'quiet': True,
        'no_warnings': True,
    }
    
    # 如果使用cookies，从Edge浏览器提取
    if use_cookies:
        ydl_opts['cookiesfrombrowser'] = ('edge', )
        print("  [INFO] 尝试从Edge浏览器提取cookies...")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # 检查是否有manifest_url（HLS流）
            if 'manifest_url' in info:
                return info['manifest_url']
            
            # 获取最佳视频流的 URL
            if 'url' in info:
                return info['url']
            elif 'formats' in info and len(info['formats']) > 0:
                # 查找HLS或DASH格式
                for fmt in info['formats']:
                    if fmt.get('protocol') in ('m3u8', 'm3u8_native', 'hls'):
                        return fmt['url']
                # 如果没有HLS，返回第一个可用格式
                return info['formats'][0]['url']
            else:
                print("[ERROR] yt-dlp: 无法获取视频流地址")
                return None
    except Exception as e:
        print(f"[ERROR] yt-dlp 获取视频流失败: {e}")
        return None

def get_stream_url(url):
    """
    获取 YouTube 视频流地址（自动选择可用引擎）
    优先尝试使用cookies，如果失败则不使用cookies重试
    """
    if USE_YTDLP:
        # 先尝试使用cookies
        result = get_stream_url_ytdlp(url, use_cookies=True)
        if result:
            return result
        # 如果失败，不使用cookies重试
        print("  [WARN] 使用cookies失败，尝试无cookie模式...")
        return get_stream_url_ytdlp(url, use_cookies=False)
    elif USE_STREAMLINK:
        return get_stream_url_streamlink(url)
    elif BACKEND == 'pytube':
        return get_stream_url_pytube(url)
    else:
        print("[ERROR] 没有可用的视频解析后端")
        return None

def capture_stream(url):
    """
    捕获并显示视频流，支持 YouTube URL、HLS 流和本地视频文件
    """
    # 检查是否是本地文件
    if url.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        # 本地视频文件
        stream_url = url
        print(f"[INFO] 使用本地视频文件: {url}")
    else:
        # YouTube/HLS 流
        stream_url = get_stream_url(url)
        
        if not stream_url:
            print("[ERROR] 无法获取视频流，程序退出")
            return
    
    print(f"视频流地址获取成功: {stream_url[:50]}...")
    
    # 使用 OpenCV 打开视频流（支持HLS/FFMPEG）
    is_hls = 'm3u8' in stream_url or 'manifest' in stream_url
    
    if is_hls:
        print(f"[INFO] 检测到HLS流，使用FFMPEG后端...")
        # 对于HLS流，使用FFMPEG后端并设置超时
        cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
    else:
        cap = cv2.VideoCapture(stream_url)
    
    if not cap.isOpened():
        print("[ERROR] 无法打开视频流")
        # 如果是HLS流，尝试回退模式
        if is_hls:
            print("[INFO] 尝试标准模式打开HLS流...")
            cap = cv2.VideoCapture(stream_url)
            if not cap.isOpened():
                print("[ERROR] 无法打开HLS流")
                return
        else:
            return
    
    print("视频流已成功打开！按 'q' 键退出")
    
    # 获取视频信息
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"视频参数: {width}x{height}, FPS: {fps}")
    
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("无法读取帧，可能网络连接中断")
                break
            
            frame_count += 1
            
            # 显示帧计数
            cv2.putText(frame, f"Frame: {frame_count}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # 显示窗口
            cv2.imshow('新宿街头 AI 脑 - 实时流', frame)
            
            # 按 'q' 键退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("用户主动退出")
                break
    
    except KeyboardInterrupt:
        print("程序被中断")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print(f"视频流已关闭，共读取 {frame_count} 帧")

def find_available_stream():
    """
    查找可用的视频流
    """
    print("[INFO] 正在查找可用的直播源...")
    
    for idx, url in enumerate(SHINJUKU_STREAM_URLS, 1):
        print(f"\n  [{idx}/{len(SHINJUKU_STREAM_URLS)}] 测试: {url}")
        
        if test_stream_url(url):
            print(f"  [OK] 成功！")
            return url
        else:
            print(f"  [FAIL] 不可用")
    
    return None

def main():
    url = None
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
        print(f"使用自定义 URL/文件: {url}")
        # 本地文件不需要测试
        if not url.endswith(('.mp4', '.avi', '.mov', '.mkv')) and not test_stream_url(url):
            print("[FAIL] 自定义 URL 不可用")
            url = None
    
    if not url:
        url = find_available_stream()
    
    if not url:
        print("\n[ERROR] 所有直播源都不可用")
        print("可能原因：")
        print("  - YouTube 访问受限（需要VPN）")
        print("  - 所有直播源都已关闭")
        print("  - 网络连接问题")
        print("\n解决方案：")
        print("  1. 提供本地视频文件: python capture_stream.py video.mp4")
        print("  2. 运行测试视频生成: python create_test_video.py")
        print("  3. 提供有效的 YouTube 直播链接")
        return
    
    print(f"\n[START] 正在启动: {url}")
    capture_stream(url)

if __name__ == "__main__":
    main()
