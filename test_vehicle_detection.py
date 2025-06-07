from vehicle_detector import VehicleDetector
import os
import time

def test_vehicle_detection():
    print("=" * 60)
    print("车辆检测系统测试")
    print("=" * 60)
    
    # 创建检测器（首次运行会自动下载YOLOv8x模型）
    print("\n初始化车辆检测器...")
    detector = VehicleDetector()
    print("✓ 检测器初始化完成")
    
    # 准备测试图片目录
    test_dir = "test_vehicles"
    os.makedirs(test_dir, exist_ok=True)
    
    print(f"\n请将包含车辆的测试图片放入 {test_dir} 目录")
    
    # 获取测试图片
    test_images = [f for f in os.listdir(test_dir) 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
    
    if not test_images:
        print(f"未在 {test_dir} 目录中找到图片文件")
        print("\n您可以放入包含以下车辆的图片进行测试：")
        print("- 汽车 (轿车、SUV等)")
        print("- 公交车")
        print("- 卡车")
        print("- 摩托车")
        return
    
    print(f"\n找到 {len(test_images)} 张测试图片")
    
    # 处理每张图片
    for img_file in test_images:
        img_path = os.path.join(test_dir, img_file)
        print(f"\n处理图片: {img_file}")
        
        try:
            # 开始计时
            start_time = time.time()
            
            # 检测车辆
            vehicles = detector.detect_vehicles(img_path)
            
            # 结束计时
            process_time = time.time() - start_time
            
            print(f"检测完成，耗时: {process_time:.2f}秒")
            print(f"检测到 {len(vehicles)} 辆车:")
            
            # 按类型统计
            vehicle_count = {}
            for v in vehicles:
                vtype = v['class_name_cn']
                if vtype not in vehicle_count:
                    vehicle_count[vtype] = 0
                vehicle_count[vtype] += 1
                
                print(f"  - {vtype}: 置信度 {v['confidence']:.2%}")
            
            # 显示统计
            if vehicle_count:
                print("\n按类型统计:")
                for vtype, count in vehicle_count.items():
                    print(f"  {vtype}: {count} 辆")
            
            # 绘制结果
            output_path = os.path.join(test_dir, f"detected_{img_file}")
            detector.draw_results(img_path, vehicles, output_path)
            print(f"结果已保存到: {output_path}")
            
        except Exception as e:
            print(f"处理失败: {str(e)}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("\n提示：")
    print("1. YOLOv8x 模型能够检测 COCO 数据集的 80 个类别")
    print("2. 车辆相关类别包括：汽车、公交车、卡车、摩托车")
    print("3. 模型在标准道路场景下准确率很高")
    print("4. 首次运行会自动下载模型文件（约 130MB）")


if __name__ == "__main__":
    test_vehicle_detection()