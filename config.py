# config.py

# YouTube 直播地址
YOUTUBE_URL = "https://www.youtube.com/watch?v=6dp-bvQ7RWo"

# 网络代理 (对于国内环境访问 YouTube 是必须的)
PROXY_URL = "http://127.0.0.1:7897"

# YOLO 模型路径
# 确保 yolov8n.pt 在当前目录下
MODEL_PATH = "yolov8n.pt"

# 目标检测配置
# COCO class IDs: 0: person, 2: car, 5: bus, 7: truck
TARGET_CLASSES = [0, 2, 5, 7]
CONF_LEVEL = 0.3

# 缓存目录
SAVE_DIR = "cache_frames"
MAX_CACHE_FILES = 50

# 重试配置
RETRY_ATTEMPTS = 3
RETRY_DELAY = 1.0
