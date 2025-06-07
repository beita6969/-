from advanced_plate_recognizer import AdvancedPlateRecognizer
import cv2
import os
import time

def test_advanced_recognizer():
    recognizer = AdvancedPlateRecognizer('best.pt')
    
    test_images_dir = 'test_images'
    os.makedirs(test_images_dir, exist_ok=True)
    
    print("高级车牌识别系统测试")
    print("=" * 60)
    print("特性:")
    print("- HyperLPR3 + EasyOCR 双引擎识别")
    print("- 透视变换校正")
    print("- 高级图像预处理")
    print("- 智能字符纠错")
    print("=" * 60)
    
    image_files = [f for f in os.listdir(test_images_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
    
    if not image_files:
        print(f"\n请在 {test_images_dir} 文件夹中放入测试图片")
        return
    
    total_time = 0
    total_plates = 0
    
    for image_file in image_files:
        image_path = os.path.join(test_images_dir, image_file)
        print(f"\n处理图片: {image_file}")
        
        try:
            start_time = time.time()
            results = recognizer.process_image(image_path)
            end_time = time.time()
            
            process_time = end_time - start_time
            total_time += process_time
            
            if not results:
                print("  未检测到车牌")
            else:
                total_plates += len(results)
                for i, result in enumerate(results):
                    print(f"\n  车牌 {i+1}:")
                    print(f"    识别结果: {result['plate_text']}")
                    print(f"    检测置信度: {result['detection_confidence']:.2%}")
                    print(f"    OCR置信度: {result['ocr_confidence']:.2%}")
                    print(f"    综合置信度: {result['overall_confidence']:.2%}")
                    
                    # 置信度评级
                    if result['overall_confidence'] > 0.8:
                        print("    评级: ⭐⭐⭐ 高置信度")
                    elif result['overall_confidence'] > 0.6:
                        print("    评级: ⭐⭐ 中等置信度")
                    else:
                        print("    评级: ⭐ 低置信度")
            
            print(f"  处理时间: {process_time:.2f}秒")
            
            # 保存结果
            output_path = os.path.join(test_images_dir, f'result_{image_file}')
            recognizer.draw_results(image_path, results, output_path)
            print(f"  结果已保存到: {output_path}")
            
        except Exception as e:
            print(f"  处理失败: {str(e)}")
    
    # 统计信息
    if total_plates > 0:
        print(f"\n" + "=" * 60)
        print(f"统计信息:")
        print(f"- 处理图片数: {len(image_files)}")
        print(f"- 检测到车牌数: {total_plates}")
        print(f"- 总处理时间: {total_time:.2f}秒")
        print(f"- 平均处理时间: {total_time/len(image_files):.2f}秒/图")

if __name__ == "__main__":
    test_advanced_recognizer()