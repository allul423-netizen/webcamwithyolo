import cv2
import numpy as np

def create_video(filename="local_test.mp4", duration=10, fps=30, width=1280, height=720):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    frames = duration * fps
    for i in range(frames):
        # Create a black image
        img = np.zeros((height, width, 3), np.uint8)
        
        # Add frame count text
        cv2.putText(img, f"Frame: {i}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        
        # Add a moving circle
        x = int((i * 10) % width)
        y = int(height / 2 + 100 * np.sin(i * 0.1))
        cv2.circle(img, (x, y), 50, (0, 0, 255), -1)

        out.write(img)
    
    out.release()
    print(f"Created {filename} ({duration}s, {width}x{height})")

if __name__ == "__main__":
    create_video()
