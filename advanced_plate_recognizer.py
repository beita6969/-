import cv2
import numpy as np
from ultralytics import YOLO
from hyperlpr3 import LicensePlateCatcher
import easyocr
from PIL import Image
import os
import re
import math

class AdvancedPlateRecognizer:
    def __init__(self, yolo_model_path='best.pt'):
        self.yolo_model = YOLO(yolo_model_path)
        
        # 初始化HyperLPR
        self.catcher = LicensePlateCatcher()
        
        # 备用的EasyOCR
        self.reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
        
        # 中国车牌正则
        self.plate_pattern = re.compile(
            r'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领A-Z]{1}'
            r'[A-Z]{1}'
            r'[A-Z0-9]{4,5}$'
        )
        
        # 省份简称映射
        self.provinces = {
            '京': '京', '津': '津', '沪': '沪', '渝': '渝', '冀': '冀',
            '豫': '豫', '云': '云', '辽': '辽', '黑': '黑', '湘': '湘',
            '皖': '皖', '鲁': '鲁', '新': '新', '苏': '苏', '浙': '浙',
            '赣': '赣', '鄂': '鄂', '桂': '桂', '甘': '甘', '晋': '晋',
            '蒙': '蒙', '陕': '陕', '吉': '吉', '闽': '闽', '贵': '贵',
            '粤': '粤', '青': '青', '藏': '藏', '川': '川', '宁': '宁',
            '琼': '琼', '使': '使', '领': '领'
        }
        
    def detect_plates(self, image_path):
        """使用YOLO检测车牌位置"""
        results = self.yolo_model(image_path)
        
        image = cv2.imread(image_path)
        plates = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    
                    # 稍微扩大检测框
                    padding = 5
                    x1 = max(0, x1 - padding)
                    y1 = max(0, y1 - padding)
                    x2 = min(image.shape[1], x2 + padding)
                    y2 = min(image.shape[0], y2 + padding)
                    
                    plate_img = image[y1:y2, x1:x2]
                    
                    plates.append({
                        'bbox': (x1, y1, x2, y2),
                        'image': plate_img,
                        'confidence': float(box.conf[0])
                    })
        
        return plates
    
    def correct_perspective(self, image):
        """透视变换校正"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 边缘检测
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # 查找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # 找到最大轮廓
            largest_contour = max(contours, key=cv2.contourArea)
            
            # 近似多边形
            epsilon = 0.02 * cv2.arcLength(largest_contour, True)
            approx = cv2.approxPolyDP(largest_contour, epsilon, True)
            
            if len(approx) == 4:
                # 获取四个角点
                pts = approx.reshape(4, 2).astype(np.float32)
                
                # 计算目标矩形
                rect = cv2.minAreaRect(pts)
                box = cv2.boxPoints(rect)
                box = np.int0(box)
                
                # 获取宽高
                width = int(rect[1][0])
                height = int(rect[1][1])
                
                if width < height:
                    width, height = height, width
                
                # 目标点
                dst_pts = np.array([[0, 0], [width-1, 0], 
                                   [width-1, height-1], [0, height-1]], dtype=np.float32)
                
                # 透视变换
                M = cv2.getPerspectiveTransform(pts, dst_pts)
                warped = cv2.warpPerspective(image, M, (width, height))
                
                return warped
        
        return image
    
    def preprocess_plate_image(self, plate_img):
        """高级图像预处理"""
        # 1. 调整大小
        height, width = plate_img.shape[:2]
        scale = 3
        plate_img = cv2.resize(plate_img, (width * scale, height * scale), 
                              interpolation=cv2.INTER_CUBIC)
        
        # 2. 透视校正
        plate_img = self.correct_perspective(plate_img)
        
        # 3. 转换为灰度图
        gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        
        # 4. 去噪
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        
        # 5. 对比度增强
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        # 6. 锐化
        kernel = np.array([[-1,-1,-1],
                          [-1, 9,-1],
                          [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        # 7. 自适应二值化
        binary = cv2.adaptiveThreshold(sharpened, 255, 
                                      cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY, 11, 2)
        
        # 8. 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        morphed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return morphed, plate_img
    
    def correct_plate_text(self, text):
        """高级字符纠正"""
        if not text:
            return text
            
        # 移除非法字符
        text = re.sub(r'[^\u4e00-\u9fa5A-Z0-9]', '', text.upper())
        
        # 第一个字符必须是省份简称
        if len(text) > 0:
            first_char = text[0]
            # 常见错误映射
            province_corrections = {
                '晋': '晋', '音': '晋', '齐': '鲁', '曾': '鲁',
                '京': '京', '浙': '浙', '沪': '沪', '粤': '粤',
                '冀': '冀', '豫': '豫', '川': '川', '鄂': '鄂',
                '湘': '湘', '赣': '赣', '闽': '闽', '黑': '黑',
                '吉': '吉', '辽': '辽', '新': '新', '藏': '藏',
                '陕': '陕', '甘': '甘', '青': '青', '宁': '宁',
                '桂': '桂', '云': '云', '贵': '贵', '琼': '琼',
                '渝': '渝', '津': '津', '蒙': '蒙', '皖': '皖',
                '苏': '苏', '使': '使', '领': '领'
            }
            
            if first_char in province_corrections:
                text = province_corrections[first_char] + text[1:]
            elif first_char not in self.provinces:
                # 如果不是有效省份，尝试匹配最相似的
                return None
        
        # 第二个字符必须是大写字母
        if len(text) > 1:
            second_char = text[1]
            # 常见数字字母混淆
            letter_corrections = {
                '0': 'D', '1': 'I', '2': 'Z', '3': 'B',
                '4': 'A', '5': 'S', '6': 'G', '7': 'T',
                '8': 'B', '9': 'G'
            }
            
            if second_char in letter_corrections:
                text = text[0] + letter_corrections[second_char] + text[2:]
            elif not second_char.isalpha():
                return None
        
        # 后续字符纠正（数字字母混淆）
        if len(text) > 2:
            corrections = {
                'O': '0', 'I': '1', 'Z': '2', 'S': '5', 
                'B': '8', 'D': '0', 'Q': '0', 'G': '6',
                'T': '7', 'L': '1', 'J': '1'
            }
            
            # 对后续字符进行纠正
            corrected = text[:2]
            for char in text[2:]:
                if char in corrections:
                    corrected += corrections[char]
                else:
                    corrected += char
            
            text = corrected
        
        # 验证格式
        if self.plate_pattern.match(text):
            return text
        
        return None
    
    def recognize_with_hyperlpr(self, image):
        """使用HyperLPR识别"""
        try:
            results = self.catcher(image)
            if results:
                # 返回置信度最高的结果
                best_result = max(results, key=lambda x: x[1])
                plate_text = best_result[0]
                confidence = best_result[1]
                
                # 纠正文本
                corrected_text = self.correct_plate_text(plate_text)
                if corrected_text:
                    return corrected_text, float(confidence)
                    
            return None, 0.0
        except Exception as e:
            print(f"HyperLPR error: {e}")
            return None, 0.0
    
    def recognize_with_easyocr(self, processed_img):
        """使用EasyOCR作为备用"""
        try:
            result = self.reader.readtext(processed_img)
            
            if not result:
                return None, 0.0
            
            texts = []
            confidences = []
            
            for (bbox, text, confidence) in result:
                texts.append(text)
                confidences.append(float(confidence))
            
            plate_text = ''.join(texts).replace(' ', '').upper()
            
            # 纠正文本
            corrected_text = self.correct_plate_text(plate_text)
            if corrected_text:
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                return corrected_text, avg_confidence
                
            return None, 0.0
        except Exception as e:
            print(f"EasyOCR error: {e}")
            return None, 0.0
    
    def recognize_plate_text(self, plate_img):
        """综合识别策略"""
        # 预处理
        processed_img, original_img = self.preprocess_plate_image(plate_img)
        
        # 策略1: 先尝试HyperLPR（原图）
        text1, conf1 = self.recognize_with_hyperlpr(plate_img)
        
        # 策略2: HyperLPR（处理后的图）
        text2, conf2 = self.recognize_with_hyperlpr(original_img)
        
        # 策略3: EasyOCR（处理后的图）
        text3, conf3 = self.recognize_with_easyocr(processed_img)
        
        # 选择最佳结果
        results = [
            (text1, conf1),
            (text2, conf2),
            (text3, conf3)
        ]
        
        # 过滤有效结果
        valid_results = [(t, c) for t, c in results if t is not None]
        
        if valid_results:
            # 返回置信度最高的结果
            best_result = max(valid_results, key=lambda x: x[1])
            return best_result
        
        return None, 0.0
    
    def process_image(self, image_path):
        """处理图片"""
        plates = self.detect_plates(image_path)
        
        results = []
        for plate in plates:
            text, ocr_confidence = self.recognize_plate_text(plate['image'])
            
            if text:
                results.append({
                    'bbox': plate['bbox'],
                    'plate_text': text,
                    'detection_confidence': float(plate['confidence']),
                    'ocr_confidence': float(ocr_confidence),
                    'overall_confidence': float(plate['confidence'] * ocr_confidence)
                })
        
        return results
    
    def draw_results(self, image_path, results, output_path=None):
        """绘制结果"""
        image = cv2.imread(image_path)
        
        # 加载支持中文的字体
        try:
            from PIL import Image, ImageDraw, ImageFont
            import numpy as np
            
            # 转换为PIL图像
            pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_img)
            
            # 尝试使用系统字体
            try:
                font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 20)
            except:
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 20)
                except:
                    font = ImageFont.load_default()
            
            for result in results:
                x1, y1, x2, y2 = result['bbox']
                
                # 根据置信度选择颜色
                if result['overall_confidence'] > 0.8:
                    color = (0, 255, 0)  # 绿色 - 高置信度
                    pil_color = (0, 255, 0)
                elif result['overall_confidence'] > 0.6:
                    color = (255, 255, 0)  # 黄色 - 中置信度
                    pil_color = (255, 255, 0)
                else:
                    color = (255, 0, 0)  # 红色 - 低置信度
                    pil_color = (255, 0, 0)
                
                # 绘制边框
                draw.rectangle([x1, y1, x2, y2], outline=pil_color, width=2)
                
                # 准备标签文本
                label = f"{result['plate_text']} ({result['overall_confidence']:.2%})"
                
                # 获取文本大小
                bbox = draw.textbbox((x1, y1 - 25), label, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # 绘制背景
                draw.rectangle([x1, y1 - text_height - 10, x1 + text_width + 10, y1], 
                             fill=pil_color)
                
                # 绘制文本
                draw.text((x1 + 5, y1 - text_height - 5), label, 
                         fill=(0, 0, 0), font=font)
            
            # 转换回OpenCV格式
            image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            
        except ImportError:
            # 如果PIL不可用，使用原始方法
            for result in results:
                x1, y1, x2, y2 = result['bbox']
                
                if result['overall_confidence'] > 0.8:
                    color = (0, 255, 0)
                elif result['overall_confidence'] > 0.6:
                    color = (0, 255, 255)
                else:
                    color = (0, 0, 255)
                
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
                
                # 只显示ASCII字符避免编码问题
                label = f"{result['plate_text']} ({result['overall_confidence']:.2%})"
                
                font_scale = 0.7
                thickness = 2
                (text_width, text_height), baseline = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
                )
                
                cv2.rectangle(image, (x1, y1 - text_height - 10), 
                             (x1 + text_width, y1), color, -1)
                cv2.putText(image, label, (x1, y1 - 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness)
        
        if output_path:
            cv2.imwrite(output_path, image)
        
        return image