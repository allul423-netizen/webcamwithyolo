import cv2
import numpy as np

# 创建测试视频 - 模拟新宿街头的交通场景
def create_test_traffic_video(filename='test_traffic.mp4', duration=30, fps=30):
    width, height = 1280, 720
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    # 颜色定义
    colors = {
        'car': (255, 150, 0),      # 橙色
        'person': (0, 255, 0),     # 绿色
        'traffic_light': (0, 0, 255)  # 红色
    }
    
    total_frames = duration * fps
    
    for frame_idx in range(total_frames):
        # 创建黑色背景
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 添加道路（灰色矩形）
        cv2.rectangle(frame, (0, height // 2 - 50), (width, height // 2 + 50), (150, 150, 150), -1)
        
        # 添加道路标线
        for i in range(0, width, 40):
            cv2.line(frame, (i, height // 2 - 10), (i + 20, height // 2 - 10), (255, 255, 255), 2)
            cv2.line(frame, (i, height // 2 + 10), (i + 20, height // 2 + 10), (255, 255, 255), 2)
        
        # 模拟移动的车辆
        num_cars = 5
        for i in range(num_cars):
            x_pos = (frame_idx * 2 + i * 200) % (width + 100) - 50
            if x_pos > 0 and x_pos < width:
                # 绘制车辆（矩形代表车辆）
                cv2.rectangle(frame, 
                             (x_pos, height // 2 - 40),
                             (x_pos + 80, height // 2 - 10), 
                             colors['car'], -1)
                cv2.putText(frame, f"Car {i+1}", (x_pos + 10, height // 2 - 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # 模拟行人
        num_people = 3
        for i in range(num_people):
            x_pos = int((frame_idx * 1.5 + i * 300) % (width + 100) - 50)
            if x_pos > 0 and x_pos < width:
                # 绘制人（圆圈代表行人）
                cv2.circle(frame, (x_pos, height // 2 - 70), 10, colors['person'], -1)
                cv2.putText(frame, f"P{i+1}", (x_pos - 10, height // 2 - 85), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors['person'], 1)
        
        # 模拟交通灯（固定在左上角）
        cv2.circle(frame, (100, 100), 20, colors['traffic_light'], -1)
        if (frame_idx // fps) % 2 == 0:
            cv2.putText(frame, "RED", (80, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, colors['traffic_light'], 2)
        else:
            cv2.putText(frame, "GREEN", (70, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # 添加帧计数
        cv2.putText(frame, f"Frame: {frame_idx}/{total_frames}", (10, height - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # 添加标题
        cv2.putText(frame, "TEST VIDEO - Simulated Shinjuku Traffic", (width // 2 - 200, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        out.write(frame)
        
        if frame_idx % 30 == 0:
            print(f"[CREATE] 生成测试视频: {frame_idx // 30}/{duration} 秒")
    
    out.release()
    print(f"[DONE] 测试视频已创建: {filename}")
    
    # 验证视频
    cap = cv2.VideoCapture(filename)
    if cap.isOpened():
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        print(f"[INFO] 视频信息: {total_frames} 帧, {fps} FPS")
        cap.release()
    else:
        print("[ERROR] 视频验证失败")

if __name__ == "__main__":
    create_test_traffic_video()
