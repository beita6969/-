import cv2
import numpy as np
from ultralytics import YOLO
from advanced_plate_recognizer import AdvancedPlateRecognizer
from vehicle_detector import VehicleDetector
import os
from datetime import datetime

class IntegratedDetector:
    """集成车辆检测和车牌识别的系统"""
    
    def __init__(self, plate_model_path='best.pt', vehicle_model_path=None):
        # 初始化车牌识别器
        self.plate_recognizer = AdvancedPlateRecognizer(plate_model_path)
        
        # 初始化车辆检测器
        self.vehicle_detector = VehicleDetector(vehicle_model_path)
        
    def process_image(self, image_path):
        """处理图片：同时检测车辆和识别车牌"""
        
        # 1. 检测车辆
        vehicles = self.vehicle_detector.detect_vehicles(image_path)
        
        # 2. 识别车牌
        plates = self.plate_recognizer.process_image(image_path)
        
        # 3. 关联车辆和车牌
        results = self._associate_vehicles_plates(vehicles, plates)
        
        return {
            'vehicles': vehicles,
            'plates': plates,
            'associated_results': results
        }
    
    def _associate_vehicles_plates(self, vehicles, plates):
        """关联车辆和车牌"""
        associated = []
        
        for vehicle in vehicles:
            vx1, vy1, vx2, vy2 = vehicle['bbox']
            vehicle_area = (vx2 - vx1) * (vy2 - vy1)
            
            # 查找车辆边框内的车牌
            associated_plates = []
            for plate in plates:
                px1, py1, px2, py2 = plate['bbox']
                
                # 检查车牌是否在车辆边框内
                if (px1 >= vx1 and py1 >= vy1 and 
                    px2 <= vx2 and py2 <= vy2):
                    associated_plates.append(plate)
                else:
                    # 检查车牌是否与车辆有重叠（容错）
                    overlap_x = max(0, min(vx2, px2) - max(vx1, px1))
                    overlap_y = max(0, min(vy2, py2) - max(vy1, py1))
                    overlap_area = overlap_x * overlap_y
                    plate_area = (px2 - px1) * (py2 - py1)
                    
                    # 如果重叠面积超过车牌面积的50%，认为属于该车辆
                    if overlap_area > 0.5 * plate_area:
                        associated_plates.append(plate)
            
            associated.append({
                'vehicle': vehicle,
                'plates': associated_plates
            })
        
        return associated
    
    def draw_integrated_results(self, image_path, results, output_path=None):
        """绘制集成检测结果"""
        image = cv2.imread(image_path)
        
        # 统计信息
        stats = {
            'total_vehicles': len(results['vehicles']),
            'total_plates': len(results['plates']),
            'vehicles_with_plates': 0,
            'vehicles_by_type': {}
        }
        
        # 绘制车辆和关联的车牌
        for assoc in results['associated_results']:
            vehicle = assoc['vehicle']
            plates = assoc['plates']
            
            # 统计
            if plates:
                stats['vehicles_with_plates'] += 1
            
            vehicle_type = vehicle['class_name_cn']
            if vehicle_type not in stats['vehicles_by_type']:
                stats['vehicles_by_type'][vehicle_type] = {'total': 0, 'with_plates': 0}
            stats['vehicles_by_type'][vehicle_type]['total'] += 1
            if plates:
                stats['vehicles_by_type'][vehicle_type]['with_plates'] += 1
            
            # 绘制车辆边框
            vx1, vy1, vx2, vy2 = vehicle['bbox']
            color = self.vehicle_detector.class_colors.get(vehicle['class_id'], (0, 255, 0))
            cv2.rectangle(image, (vx1, vy1), (vx2, vy2), color, 2)
            
            # 不绘制文字标签，避免中文乱码
            
            # 绘制车牌边框（如果有）
            for plate in plates:
                px1, py1, px2, py2 = plate['bbox']
                # 车牌用不同颜色的细边框
                cv2.rectangle(image, (px1, py1), (px2, py2), (255, 255, 0), 1)
        
        # 绘制统计信息
        self._draw_stats(image, stats)
        
        if output_path:
            cv2.imwrite(output_path, image)
        
        return image, stats
    
    def _draw_stats(self, image, stats):
        """在图片上绘制统计信息"""
        # 不在图片上绘制统计信息，避免中文乱码
        pass


# 测试代码
if __name__ == "__main__":
    # 创建集成检测器
    detector = IntegratedDetector()
    
    # 测试图片
    test_image = "test_image.jpg"
    if os.path.exists(test_image):
        print("正在处理图片...")
        results = detector.process_image(test_image)
        
        print(f"\n检测结果:")
        print(f"- 车辆数量: {len(results['vehicles'])}")
        print(f"- 车牌数量: {len(results['plates'])}")
        
        # 绘制结果
        output_image, stats = detector.draw_integrated_results(
            test_image, results, "integrated_result.jpg"
        )
        
        print("\n详细统计:")
        for vehicle_type, counts in stats['vehicles_by_type'].items():
            print(f"- {vehicle_type}: {counts['total']} 辆 (其中 {counts['with_plates']} 辆有车牌)")
        
        print("\n结果已保存到: integrated_result.jpg")