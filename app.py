from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
from advanced_plate_recognizer import AdvancedPlateRecognizer as LicensePlateRecognizer
import os
import cv2
import base64
from io import BytesIO
from PIL import Image
import numpy as np

app = Flask(__name__)
CORS(app)

recognizer = LicensePlateRecognizer('best.pt')

UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>中国车牌识别系统</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .upload-area {
            border: 2px dashed #ddd;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            margin: 20px 0;
            cursor: pointer;
            transition: border-color 0.3s;
        }
        .upload-area:hover {
            border-color: #4CAF50;
        }
        .upload-area.dragover {
            border-color: #4CAF50;
            background-color: #f0f8ff;
        }
        input[type="file"] {
            display: none;
        }
        .btn {
            background-color: #4CAF50;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px;
        }
        .btn:hover {
            background-color: #45a049;
        }
        .btn:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        .results {
            margin-top: 30px;
        }
        .result-item {
            background-color: #f9f9f9;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #4CAF50;
        }
        .plate-text {
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin: 10px 0;
        }
        .confidence {
            color: #666;
            font-size: 14px;
        }
        .image-container {
            margin: 20px 0;
            text-align: center;
        }
        .image-container img {
            max-width: 100%;
            border-radius: 5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .loading {
            display: none;
            text-align: center;
            margin: 20px 0;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #4CAF50;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚗 中国车牌识别系统</h1>
        
        <div class="upload-area" id="uploadArea">
            <p>点击或拖拽图片到此处上传</p>
            <p style="color: #666; font-size: 14px;">支持 JPG, PNG, BMP 格式</p>
            <input type="file" id="fileInput" accept="image/*">
        </div>
        
        <div style="text-align: center;">
            <button class="btn" onclick="selectFile()">选择图片</button>
            <button class="btn" id="processBtn" onclick="processImage()" disabled>开始识别</button>
        </div>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>正在识别中，请稍候...</p>
        </div>
        
        <div id="preview" class="image-container"></div>
        
        <div id="results" class="results"></div>
    </div>

    <script>
        let selectedFile = null;
        
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const processBtn = document.getElementById('processBtn');
        const loading = document.getElementById('loading');
        const preview = document.getElementById('preview');
        const results = document.getElementById('results');
        
        uploadArea.addEventListener('click', () => fileInput.click());
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFile(files[0]);
            }
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFile(e.target.files[0]);
            }
        });
        
        function selectFile() {
            fileInput.click();
        }
        
        function handleFile(file) {
            if (!file.type.startsWith('image/')) {
                alert('请选择图片文件！');
                return;
            }
            
            selectedFile = file;
            processBtn.disabled = false;
            
            const reader = new FileReader();
            reader.onload = (e) => {
                preview.innerHTML = `<img src="${e.target.result}" alt="预览图">`;
                results.innerHTML = '';
            };
            reader.readAsDataURL(file);
        }
        
        async function processImage() {
            if (!selectedFile) return;
            
            loading.style.display = 'block';
            processBtn.disabled = true;
            results.innerHTML = '';
            
            const formData = new FormData();
            formData.append('image', selectedFile);
            
            try {
                const response = await fetch('/recognize', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.error) {
                    alert('识别失败：' + data.error);
                } else {
                    displayResults(data);
                }
            } catch (error) {
                alert('请求失败：' + error.message);
            } finally {
                loading.style.display = 'none';
                processBtn.disabled = false;
            }
        }
        
        function displayResults(data) {
            results.innerHTML = '<h2>识别结果</h2>';
            
            if (data.result_image) {
                preview.innerHTML = `<img src="data:image/jpeg;base64,${data.result_image}" alt="识别结果">`;
            }
            
            if (data.plates.length === 0) {
                results.innerHTML += '<p style="text-align: center; color: #666;">未检测到车牌</p>';
            } else {
                data.plates.forEach((plate, index) => {
                    const resultHtml = `
                        <div class="result-item">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div class="plate-text">车牌 ${index + 1}: ${plate.plate_text || '无法识别'}</div>
                                    <div class="confidence">
                                        检测置信度: ${(plate.detection_confidence * 100).toFixed(1)}%<br>
                                        OCR置信度: ${(plate.ocr_confidence * 100).toFixed(1)}%<br>
                                        综合置信度: ${(plate.overall_confidence * 100).toFixed(1)}%
                                    </div>
                                </div>
                                <div style="color: ${plate.overall_confidence > 0.8 ? '#4CAF50' : '#ff9800'}; font-size: 24px;">
                                    ${plate.overall_confidence > 0.8 ? '✓' : '⚠'}
                                </div>
                            </div>
                        </div>
                    `;
                    results.innerHTML += resultHtml;
                });
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/recognize', methods=['POST'])
def recognize():
    try:
        if 'image' not in request.files:
            return jsonify({'error': '没有上传图片'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400
        
        filename = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filename)
        
        results = recognizer.process_image(filename)
        
        output_path = os.path.join(RESULTS_FOLDER, f'result_{file.filename}')
        result_image = recognizer.draw_results(filename, results, output_path)
        
        _, buffer = cv2.imencode('.jpg', result_image)
        result_image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        response = {
            'plates': results,
            'result_image': result_image_base64
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)