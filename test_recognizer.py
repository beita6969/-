from license_plate_recognizer import LicensePlateRecognizer
import cv2
import os

def test_recognizer():
    recognizer = LicensePlateRecognizer('best.pt')
    
    test_images_dir = 'test_images'
    os.makedirs(test_images_dir, exist_ok=True)
    
    print("车牌识别系统测试")
    print("-" * 50)
    
    image_files = [f for f in os.listdir(test_images_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
    
    if not image_files:
        print(f"请在 {test_images_dir} 文件夹中放入测试图片")
        return
    
    for image_file in image_files:
        image_path = os.path.join(test_images_dir, image_file)
        print(f"\n处理图片: {image_file}")
        
        try:
            results = recognizer.process_image(image_path)
            
            if not results:
                print("  未检测到车牌")
            else:
                for i, result in enumerate(results):
                    print(f"\n  车牌 {i+1}:")
                    print(f"    识别结果: {result['plate_text']}")
                    print(f"    检测置信度: {result['detection_confidence']:.2%}")
                    print(f"    OCR置信度: {result['ocr_confidence']:.2%}")
                    print(f"    综合置信度: {result['overall_confidence']:.2%}")
            
            output_path = os.path.join(test_images_dir, f'result_{image_file}')
            recognizer.draw_results(image_path, results, output_path)
            print(f"  结果已保存到: {output_path}")
            
        except Exception as e:
            print(f"  处理失败: {str(e)}")

if __name__ == "__main__":
    test_recognizer()