import os
import time
import glob
import cv2
import torch
import threading
import subprocess
import shutil
from ultralytics import YOLO

# ==========================================
# 配置区域 (Configuration)
# ==========================================
# YouTube 直播地址 (Shinjuku)
YOUTUBE_URL = "https://www.youtube.com/watch?v=6dp-bvQ7RWo"

# 本地代理 (Streamlink 和 FFmpeg 需要)
PROXY_URL = "http://127.0.0.1:7897" 

# 缓存目录
SAVE_DIR = "cache_frames"
MAX_CACHE_FILES = 50

# YOLO 模型路径
MODEL_PATH = "yolov8n.pt"
CONF_LEVEL = 0.3
TARGET_CLASSES = [0, 2, 5, 7] # person, car, bus, truck

# ==========================================
# 辅助函数
# ==========================================
def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_latest_file(directory):
    files = glob.glob(os.path.join(directory, "shinjuku_*.jpg"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)

# ==========================================
# 线程 1: 视频流抓取 (Producer)
# ==========================================
class FrameFetcher(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.stop_event = threading.Event()
        self.cached_stream_url = None
        ensure_dir(SAVE_DIR)

    def get_real_stream_url(self):
        """使用 Streamlink 获取真实的流地址"""
        print(f"[{time.strftime('%H:%M:%S')}] 📡 正在解析直播流 (Streamlink)...")
        cmd = [
            "streamlink",
            "--http-proxy", PROXY_URL,
            "--stream-url", 
            YOUTUBE_URL,
            "480p,best"
        ]
        try:
            # 创建不显示窗口的 startupinfo (Windows专用)
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            res = subprocess.run(cmd, capture_output=True, text=True, check=True, startupinfo=startupinfo)
            url = res.stdout.strip()
            if "googlevideo.com" in url:
                return url
        except Exception as e:
            print(f"❌ 解析流地址失败: {e}")
        return None

    def capture_frame(self):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        final_path = os.path.join(SAVE_DIR, f"shinjuku_{timestamp}.jpg")
        temp_path = os.path.join(SAVE_DIR, "temp_streamlink.jpg")

        if not self.cached_stream_url:
            self.cached_stream_url = self.get_real_stream_url()
        
        if not self.cached_stream_url:
            return

        # FFmpeg 抓帧命令
        cmd = [
            "ffmpeg",
            "-y",
            "-http_proxy", PROXY_URL,
            "-i", self.cached_stream_url,
            "-frames:v", "1",
            "-q:v", "2",
            temp_path
        ]

        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10, startupinfo=startupinfo)
            
            if os.path.exists(temp_path):
                # 原子操作重命名，防止读取不完整
                os.replace(temp_path, final_path)
                print(f"✅ 捕获成功: {os.path.basename(final_path)}")
            else:
                self.cached_stream_url = None # 失败可能因为URL过期
        except Exception as e:
            print(f"⚠️ 截帧异常: {e}")
            self.cached_stream_url = None

    def cleanup_old_files(self):
        files = sorted(glob.glob(os.path.join(SAVE_DIR, "shinjuku_*.jpg")), key=os.path.getmtime)
        while len(files) > MAX_CACHE_FILES:
            try:
                os.remove(files.pop(0))
            except:
                pass

    def run(self):
        print("🚀 启动后台抓取线程...")
        while not self.stop_event.is_set():
            try:
                self.capture_frame()
                self.cleanup_old_files()
            except Exception as e:
                print(f"抓取线程错误: {e}")
            
            # 间隔 2 秒
            time.sleep(2)

    def stop(self):
        self.stop_event.set()

# ==========================================
# 主程序: YOLO 检测与显示 (Consumer)
# ==========================================
def main():
    print(f"[{time.strftime('%H:%M:%S')}] 🧠 正在加载 YOLO 模型...")

    # Torch Load Patch (Windows Safe Load fix)
    original_torch_load = torch.load
    def patched_torch_load(*args, **kwargs):
        kwargs['weights_only'] = False 
        return original_torch_load(*args, **kwargs)
    torch.load = patched_torch_load

    try:
        model = YOLO(MODEL_PATH)
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"✅ 模型加载成功！运行设备: {device}")
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return

    # 启动抓取线程
    fetcher = FrameFetcher()
    fetcher.start()

    # GUI 窗口设置
    cv2.namedWindow('Shinjuku AI Monitor', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Shinjuku AI Monitor', 1280, 720)
    
    last_processed_file = ""
    print("📡 监控已就绪，按 'q' 退出...")

    try:
        while True:
            latest_file = get_latest_file(SAVE_DIR)
            
            if latest_file and latest_file != last_processed_file:
                # 给写入一点缓冲时间
                time.sleep(0.1)
                
                frame = cv2.imread(latest_file)
                if frame is not None:
                    # YOLO 推理
                    results = model(frame, conf=CONF_LEVEL, classes=TARGET_CLASSES, verbose=False)
                    annotated_frame = results[0].plot()
                    
                    # 统计信息
                    num_objects = len(results[0].boxes)
                    timestamp = time.strftime('%H:%M:%S')
                    
                    # 绘制文字
                    cv2.putText(annotated_frame, f"Objects: {num_objects} | Time: {timestamp}", (20, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                    
                    cv2.imshow('Shinjuku AI Monitor', annotated_frame)
                    last_processed_file = latest_file
                    print(f"[{timestamp}] 检测到 {num_objects} 个目标")
            
            if cv2.waitKey(100) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("\n👋 用户中断...")
    finally:
        print("正在停止抓取线程...")
        fetcher.stop()
        fetcher.join()
        cv2.destroyAllWindows()
        print("程已退出。")

if __name__ == "__main__":
    main()
