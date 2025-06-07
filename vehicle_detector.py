import cv2
import numpy as np
from ultralytics import YOLO
import os
from datetime import datetime

class VehicleDetector:
    def __init__(self, model_path=None):
        """
        初始化车辆检测器
        使用YOLOv8x模型以获得最高准确率
        """
        if model_path and os.path.exists(model_path):
            self.model = YOLO(model_path)
        else:
            # 自动下载YOLOv8x预训练模型（最高准确率）
            print("正在下载YOLOv8x预训练模型...")
            self.model = YOLO('yolov8x.pt')
            print("模型下载完成！")
        
        # COCO数据集中的车辆类别
        self.vehicle_classes = {
            2: 'car',        # 汽车
            3: 'motorcycle', # 摩托车
            5: 'bus',        # 公交车
            7: 'truck',      # 卡车
        }
        
        # 类别对应的中文名称
        self.vehicle_classes_cn = {
            2: '汽车',
            3: '摩托车',
            5: '公交车',
            7: '卡车',
        }
        
        # 类别颜色
        self.class_colors = {
            2: (0, 255, 0),     # 汽车 - 绿色
            3: (255, 0, 0),     # 摩托车 - 蓝色
            5: (0, 255, 255),   # 公交车 - 黄色
            7: (255, 0, 255),   # 卡车 - 紫色
        }
    
    def detect_vehicles(self, image_path):
        """检测图片中的车辆"""
        results = self.model(image_path)
        
        image = cv2.imread(image_path)
        vehicles = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    class_id = int(box.cls[0])
                    
                    # 只保留车辆类别
                    if class_id in self.vehicle_classes:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        
                        vehicles.append({
                            'bbox': (x1, y1, x2, y2),
                            'class_id': class_id,
                            'class_name': self.vehicle_classes[class_id],
                            'class_name_cn': self.vehicle_classes_cn[class_id],
                            'confidence': float(box.conf[0])
                        })
        
        return vehicles
    
    def draw_results(self, image_path, vehicles, output_path=None):
        """在图片上绘制检测结果"""
        image = cv2.imread(image_path)
        
        for vehicle in vehicles:
            x1, y1, x2, y2 = vehicle['bbox']
            class_id = vehicle['class_id']
            
            # 获取颜色
            color = self.class_colors.get(class_id, (0, 255, 0))
            
            # 绘制边框
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        
        if output_path:
            cv2.imwrite(output_path, image)
        
        return image
    
    def process_video(self, video_path, output_path=None):
        """处理视频中的车辆检测"""
        cap = cv2.VideoCapture(video_path)
        
        # 获取视频属性
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 创建视频写入器
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # 每隔几帧处理一次（提高处理速度）
            if frame_count % 2 == 0:
                # 检测车辆
                temp_path = f"temp_frame_{frame_count}.jpg"
                cv2.imwrite(temp_path, frame)
                
                vehicles = self.detect_vehicles(temp_path)
                frame = self.draw_results(temp_path, vehicles)
                
                os.remove(temp_path)
            
            # 写入输出视频
            if output_path:
                out.write(frame)
            
            # 显示结果（可选）
            # cv2.imshow('Vehicle Detection', frame)
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break
        
        cap.release()
        if output_path:
            out.release()
        cv2.destroyAllWindows()


# 使用示例
if __name__ == "__main__":
    # 创建检测器
    detector = VehicleDetector()
    
    # 测试图片检测
    test_image = "test_vehicle.jpg"
    if os.path.exists(test_image):
        vehicles = detector.detect_vehicles(test_image)
        print(f"检测到 {len(vehicles)} 辆车:")
        for v in vehicles:
            print(f"- {v['class_name_cn']}: {v['confidence']:.2%}")
        
        # 绘制结果
        detector.draw_results(test_image, vehicles, "result_vehicle.jpg")