import cv2
import numpy as np
from ultralytics import YOLO
from paddleocr import PaddleOCR
from PIL import Image, ImageDraw, ImageFont
import os
import re

class LicensePlateRecognizer:
    def __init__(self, yolo_model_path='best.pt'):
        self.yolo_model = YOLO(yolo_model_path)
        self.ocr = PaddleOCR(lang='ch')
        
        self.plate_pattern = re.compile(
            r'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领A-Z]{1}'
            r'[A-Z]{1}'
            r'[A-Z0-9]{4,5}$'
        )
        
    def detect_plates(self, image_path):
        results = self.yolo_model(image_path)
        
        image = cv2.imread(image_path)
        plates = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    
                    plate_img = image[y1:y2, x1:x2]
                    
                    plates.append({
                        'bbox': (x1, y1, x2, y2),
                        'image': plate_img,
                        'confidence': float(box.conf[0])
                    })
        
        return plates
    
    def preprocess_plate_image(self, plate_img):
        height, width = plate_img.shape[:2]
        
        scale = 3
        plate_img = cv2.resize(plate_img, (width * scale, height * scale), interpolation=cv2.INTER_CUBIC)
        
        gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        
        denoised = cv2.fastNlMeansDenoising(gray)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        kernel = np.ones((1, 1), np.uint8)
        morphed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return morphed
    
    def recognize_plate_text(self, plate_img):
        processed_img = self.preprocess_plate_image(plate_img)
        
        result = self.ocr.ocr(processed_img, cls=True)
        
        if not result or not result[0]:
            return None, 0.0
        
        texts = []
        confidences = []
        
        for line in result[0]:
            text = line[1][0]
            confidence = line[1][1]
            texts.append(text)
            confidences.append(confidence)
        
        plate_text = ''.join(texts).replace(' ', '').upper()
        
        plate_text = re.sub(r'[^\u4e00-\u9fa5A-Z0-9]', '', plate_text)
        
        if self.plate_pattern.match(plate_text):
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            return plate_text, avg_confidence
        
        corrected_text = self.correct_common_mistakes(plate_text)
        if self.plate_pattern.match(corrected_text):
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            return corrected_text, avg_confidence * 0.9
        
        return plate_text, sum(confidences) / len(confidences) if confidences else 0
    
    def correct_common_mistakes(self, text):
        corrections = {
            'O': '0', 'I': '1', 'Z': '2', 'S': '5', 'B': '8',
            'D': '0', 'Q': '0', 'G': '6', 'J': '1'
        }
        
        if len(text) >= 3:
            for old, new in corrections.items():
                text = text[0:2] + text[2:].replace(old, new)
        
        return text
    
    def process_image(self, image_path):
        plates = self.detect_plates(image_path)
        
        results = []
        for plate in plates:
            text, ocr_confidence = self.recognize_plate_text(plate['image'])
            
            results.append({
                'bbox': plate['bbox'],
                'plate_text': text,
                'detection_confidence': plate['confidence'],
                'ocr_confidence': ocr_confidence,
                'overall_confidence': plate['confidence'] * ocr_confidence
            })
        
        return results
    
    def draw_results(self, image_path, results, output_path=None):
        image = cv2.imread(image_path)
        
        for result in results:
            x1, y1, x2, y2 = result['bbox']
            
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            label = f"{result['plate_text']} ({result['overall_confidence']:.2%})"
            
            font_scale = 0.7
            thickness = 2
            (text_width, text_height), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
            )
            
            cv2.rectangle(image, (x1, y1 - text_height - 10), 
                         (x1 + text_width, y1), (0, 255, 0), -1)
            cv2.putText(image, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness)
        
        if output_path:
            cv2.imwrite(output_path, image)
        
        return image