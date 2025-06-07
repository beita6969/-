from flask import Flask, request, jsonify, send_file, render_template_string, Response
from flask_cors import CORS
from advanced_plate_recognizer import AdvancedPlateRecognizer
from database import PlateDatabase
import os
import cv2
import base64
from io import BytesIO, StringIO
from PIL import Image
import numpy as np
from datetime import datetime, timedelta
import json

app = Flask(__name__)
CORS(app)

recognizer = AdvancedPlateRecognizer('best.pt')
db = PlateDatabase()

UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

ADVANCED_HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智能车牌识别管理系统</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f0f2f5;
            color: #333;
        }
        
        .header {
            background: linear-gradient(135deg, #4CAF50 0%, #2196F3 100%);
            color: white;
            padding: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .nav-tabs {
            background: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .nav-tabs ul {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0;
            list-style: none;
            display: flex;
        }
        
        .nav-tabs li {
            flex: 1;
        }
        
        .nav-tabs button {
            width: 100%;
            padding: 15px;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 16px;
            color: #666;
            transition: all 0.3s;
            border-bottom: 3px solid transparent;
        }
        
        .nav-tabs button:hover {
            background-color: #f5f5f5;
        }
        
        .nav-tabs button.active {
            color: #2196F3;
            border-bottom-color: #2196F3;
            font-weight: 600;
        }
        
        .container {
            max-width: 1400px;
            margin: 20px auto;
            padding: 0 20px;
        }
        
        .tab-content {
            display: none;
            animation: fadeIn 0.3s;
        }
        
        .tab-content.active {
            display: block;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            text-align: center;
            transition: transform 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-card i {
            font-size: 40px;
            margin-bottom: 10px;
        }
        
        .stat-card .value {
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .stat-card .label {
            color: #666;
            font-size: 14px;
        }
        
        .upload-area {
            border: 2px dashed #ddd;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .upload-area:hover {
            border-color: #4CAF50;
            background-color: #f9f9f9;
        }
        
        .upload-area.dragover {
            border-color: #4CAF50;
            background-color: #e8f5e9;
        }
        
        .btn {
            background-color: #4CAF50;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn:hover {
            background-color: #45a049;
        }
        
        .btn-secondary {
            background-color: #6c757d;
        }
        
        .btn-secondary:hover {
            background-color: #5a6268;
        }
        
        .table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        .table th,
        .table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        .table th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #666;
        }
        
        .table tr:hover {
            background-color: #f5f5f5;
        }
        
        .search-box {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .search-box input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        
        .chart-container {
            height: 300px;
            margin: 20px 0;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
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
        
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .badge-success {
            background-color: #d4edda;
            color: #155724;
        }
        
        .badge-warning {
            background-color: #fff3cd;
            color: #856404;
        }
        
        .badge-danger {
            background-color: #f8d7da;
            color: #721c24;
        }
        
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }
        
        .modal-content {
            background-color: white;
            margin: 50px auto;
            padding: 20px;
            border-radius: 10px;
            width: 80%;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
        }
        
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .close:hover {
            color: black;
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <h1><i class="fas fa-car"></i> 智能车牌识别管理系统</h1>
            <div id="currentTime"></div>
        </div>
    </div>
    
    <nav class="nav-tabs">
        <ul>
            <li><button class="tab-btn active" onclick="showTab('recognition')">
                <i class="fas fa-camera"></i> 车牌识别
            </button></li>
            <li><button class="tab-btn" onclick="showTab('dashboard')">
                <i class="fas fa-chart-line"></i> 数据统计
            </button></li>
            <li><button class="tab-btn" onclick="showTab('history')">
                <i class="fas fa-history"></i> 历史记录
            </button></li>
            <li><button class="tab-btn" onclick="showTab('search')">
                <i class="fas fa-search"></i> 车牌查询
            </button></li>
            <li><button class="tab-btn" onclick="showTab('monitor')">
                <i class="fas fa-desktop"></i> 实时监控
            </button></li>
            <li><button class="tab-btn" onclick="showTab('performance')">
                <i class="fas fa-tachometer-alt"></i> 性能指标
            </button></li>
        </ul>
    </nav>
    
    <div class="container">
        <!-- 车牌识别 -->
        <div id="recognition" class="tab-content active">
            <div class="card">
                <h2>车牌识别</h2>
                <div class="upload-area" id="uploadArea">
                    <i class="fas fa-cloud-upload-alt" style="font-size: 48px; color: #4CAF50; display: block; margin-bottom: 20px;"></i>
                    <p>点击或拖拽图片到此处上传</p>
                    <p style="color: #666; font-size: 14px;">支持 JPG, PNG, BMP 格式</p>
                    <input type="file" id="fileInput" accept="image/*" style="display: none;">
                </div>
                
                <div style="text-align: center; margin: 20px 0;">
                    <button class="btn" onclick="selectFile()">
                        <i class="fas fa-folder-open"></i> 选择图片
                    </button>
                    <button class="btn" id="processBtn" onclick="processImage()" disabled>
                        <i class="fas fa-play"></i> 开始识别
                    </button>
                </div>
                
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p>正在识别中，请稍候...</p>
                </div>
                
                <div id="preview" style="margin: 20px 0;"></div>
                <div id="results"></div>
            </div>
        </div>
        
        <!-- 数据统计 -->
        <div id="dashboard" class="tab-content">
            <div class="stats-grid" id="statsGrid">
                <div class="stat-card">
                    <i class="fas fa-car" style="color: #4CAF50;"></i>
                    <div class="value" id="totalDetections">0</div>
                    <div class="label">今日检测总数</div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-id-card" style="color: #2196F3;"></i>
                    <div class="value" id="uniqueVehicles">0</div>
                    <div class="label">独立车辆数</div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-parking" style="color: #FF9800;"></i>
                    <div class="value" id="vehiclesInPark">0</div>
                    <div class="label">在场车辆</div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-percentage" style="color: #9C27B0;"></i>
                    <div class="value" id="avgConfidence">0%</div>
                    <div class="label">平均识别率</div>
                </div>
            </div>
            
            <div class="card">
                <h3>省份分布</h3>
                <div class="chart-container">
                    <canvas id="provinceChart"></canvas>
                </div>
            </div>
            
            <div class="card">
                <h3>时段分布</h3>
                <div class="chart-container">
                    <canvas id="hourChart"></canvas>
                </div>
            </div>
        </div>
        
        <!-- 历史记录 -->
        <div id="history" class="tab-content">
            <div class="card">
                <h2>历史记录</h2>
                <div class="search-box">
                    <input type="text" id="historySearch" placeholder="搜索车牌号...">
                    <input type="date" id="startDate">
                    <input type="date" id="endDate">
                    <button class="btn" onclick="searchHistory()">
                        <i class="fas fa-search"></i> 搜索
                    </button>
                    <button class="btn btn-secondary" onclick="exportData()">
                        <i class="fas fa-download"></i> 导出
                    </button>
                </div>
                
                <table class="table">
                    <thead>
                        <tr>
                            <th>车牌号</th>
                            <th>检测时间</th>
                            <th>置信度</th>
                            <th>省份</th>
                            <th>类型</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody id="historyTable">
                    </tbody>
                </table>
                
                <div style="text-align: center; margin-top: 20px;">
                    <button class="btn" onclick="loadMoreHistory()">加载更多</button>
                </div>
            </div>
        </div>
        
        <!-- 车牌查询 -->
        <div id="search" class="tab-content">
            <div class="card">
                <h2>车牌查询</h2>
                <div class="search-box">
                    <input type="text" id="plateSearch" placeholder="输入完整车牌号...">
                    <button class="btn" onclick="searchPlate()">
                        <i class="fas fa-search"></i> 查询
                    </button>
                </div>
                
                <div id="plateSearchResults"></div>
            </div>
        </div>
        
        <!-- 实时监控 -->
        <div id="monitor" class="tab-content">
            <div class="card">
                <h2>实时监控</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <i class="fas fa-clock" style="color: #4CAF50;"></i>
                        <div class="value" id="lastHourCount">0</div>
                        <div class="label">最近一小时</div>
                    </div>
                </div>
                
                <h3>最新识别记录</h3>
                <table class="table">
                    <thead>
                        <tr>
                            <th>车牌号</th>
                            <th>时间</th>
                            <th>置信度</th>
                            <th>状态</th>
                        </tr>
                    </thead>
                    <tbody id="realtimeTable">
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- 性能指标 -->
        <div id="performance" class="tab-content">
            <div class="card">
                <h2>系统性能指标</h2>
                
                <div id="performanceTables">
                    <div class="loading" style="display: block;">
                        <div class="spinner"></div>
                        <p>加载性能数据中...</p>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 20px;">
                    <button class="btn" onclick="refreshPerformance()">
                        <i class="fas fa-sync"></i> 刷新数据
                    </button>
                    <button class="btn btn-secondary" onclick="downloadPerformanceReport()">
                        <i class="fas fa-download"></i> 下载报告
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- 详情模态框 -->
    <div id="detailModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <div id="modalContent"></div>
        </div>
    </div>

    <script>
        let selectedFile = null;
        let historyOffset = 0;
        let provinceChart = null;
        let hourChart = null;
        
        // 显示标签页
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
            
            // 加载对应的数据
            if (tabName === 'dashboard') {
                loadStatistics();
            } else if (tabName === 'history') {
                loadHistory();
            } else if (tabName === 'monitor') {
                startRealtimeMonitor();
            } else if (tabName === 'performance') {
                loadPerformance();
            }
        }
        
        // 文件上传相关
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
                preview.innerHTML = `<img src="${e.target.result}" style="max-width: 100%; border-radius: 10px;">`;
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
            results.innerHTML = '<h3>识别结果</h3>';
            
            if (data.result_image) {
                preview.innerHTML = `<img src="data:image/jpeg;base64,${data.result_image}" style="max-width: 100%; border-radius: 10px;">`;
            }
            
            // 显示车辆检测统计
            if (data.stats) {
                let statsHtml = '<div class="card" style="margin-bottom: 20px;">';
                statsHtml += '<h4>检测统计</h4>';
                statsHtml += '<div style="display: flex; gap: 20px; flex-wrap: wrap;">';
                statsHtml += `<div><strong>车辆总数:</strong> ${data.stats.total_vehicles}</div>`;
                statsHtml += `<div><strong>车牌总数:</strong> ${data.stats.total_plates}</div>`;
                statsHtml += `<div><strong>有车牌车辆:</strong> ${data.stats.vehicles_with_plates}</div>`;
                statsHtml += '</div>';
                
                if (data.stats.vehicles_by_type && Object.keys(data.stats.vehicles_by_type).length > 0) {
                    statsHtml += '<div style="margin-top: 10px;"><strong>车辆类型分布:</strong></div>';
                    statsHtml += '<div style="display: flex; gap: 15px; flex-wrap: wrap; margin-top: 5px;">';
                    for (const [type, counts] of Object.entries(data.stats.vehicles_by_type)) {
                        statsHtml += `<div class="badge badge-success" style="padding: 8px 12px;">
                            ${type}: ${counts.total} (${counts.with_plates}有牌)
                        </div>`;
                    }
                    statsHtml += '</div>';
                }
                
                statsHtml += '</div>';
                results.innerHTML += statsHtml;
            }
            
            // 显示车牌识别结果
            if (data.plates.length === 0 && data.vehicles.length === 0) {
                results.innerHTML += '<p style="text-align: center; color: #666;">未检测到车辆或车牌</p>';
            } else {
                if (data.vehicles && data.vehicles.length > 0) {
                    results.innerHTML += `<div class="card" style="margin-top: 10px;">
                        <h4>检测到 ${data.vehicles.length} 辆车</h4>
                        <p style="color: #666;">车辆已在图片中用不同颜色框出标记</p>
                    </div>`;
                }
                
                if (data.plates.length > 0) {
                    data.plates.forEach((plate, index) => {
                        let confidenceBadge = 'badge-danger';
                        if (plate.overall_confidence > 0.8) confidenceBadge = 'badge-success';
                        else if (plate.overall_confidence > 0.6) confidenceBadge = 'badge-warning';
                        
                        const resultHtml = `
                            <div class="card" style="margin-top: 10px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <h4>车牌 ${index + 1}: ${plate.plate_text || '无法识别'}</h4>
                                        <p>检测置信度: ${(plate.detection_confidence * 100).toFixed(1)}%</p>
                                        <p>OCR置信度: ${(plate.ocr_confidence * 100).toFixed(1)}%</p>
                                        <p>综合置信度: <span class="badge ${confidenceBadge}">${(plate.overall_confidence * 100).toFixed(1)}%</span></p>
                                    </div>
                                    <i class="fas fa-check-circle" style="font-size: 48px; color: ${plate.overall_confidence > 0.8 ? '#4CAF50' : '#ff9800'};"></i>
                                </div>
                            </div>
                        `;
                        results.innerHTML += resultHtml;
                    });
                }
            }
        }
        
        // 加载统计数据
        async function loadStatistics() {
            try {
                const response = await fetch('/api/statistics');
                const data = await response.json();
                
                // 更新统计卡片
                document.getElementById('totalDetections').textContent = data.total_detections;
                document.getElementById('uniqueVehicles').textContent = data.unique_vehicles;
                document.getElementById('vehiclesInPark').textContent = data.vehicles_in_park;
                document.getElementById('avgConfidence').textContent = (data.avg_confidence * 100).toFixed(1) + '%';
                
                // 更新图表
                updateProvinceChart(data.province_distribution);
                updateHourChart(data.hour_distribution);
            } catch (error) {
                console.error('加载统计数据失败:', error);
            }
        }
        
        // 更新省份分布图表
        function updateProvinceChart(data) {
            const ctx = document.getElementById('provinceChart').getContext('2d');
            
            if (provinceChart) {
                provinceChart.destroy();
            }
            
            provinceChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: Object.keys(data),
                    datasets: [{
                        label: '车辆数',
                        data: Object.values(data),
                        backgroundColor: 'rgba(76, 175, 80, 0.6)',
                        borderColor: 'rgba(76, 175, 80, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        
        // 更新时段分布图表
        function updateHourChart(data) {
            const ctx = document.getElementById('hourChart').getContext('2d');
            
            if (hourChart) {
                hourChart.destroy();
            }
            
            const hours = Array.from({length: 24}, (_, i) => i);
            const values = hours.map(h => data[h] || 0);
            
            hourChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: hours.map(h => h + ':00'),
                    datasets: [{
                        label: '检测数量',
                        data: values,
                        borderColor: 'rgba(33, 150, 243, 1)',
                        backgroundColor: 'rgba(33, 150, 243, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        
        // 加载历史记录
        async function loadHistory(reset = false) {
            if (reset) historyOffset = 0;
            
            try {
                const response = await fetch(`/api/history?offset=${historyOffset}`);
                const data = await response.json();
                
                const tbody = document.getElementById('historyTable');
                if (reset) tbody.innerHTML = '';
                
                data.records.forEach(record => {
                    const row = `
                        <tr>
                            <td>${record.plate_number}</td>
                            <td>${new Date(record.detection_time).toLocaleString()}</td>
                            <td><span class="badge ${record.confidence > 0.8 ? 'badge-success' : 'badge-warning'}">${(record.confidence * 100).toFixed(1)}%</span></td>
                            <td>${record.province}</td>
                            <td>${record.plate_type}</td>
                            <td>
                                <button class="btn" style="padding: 5px 10px;" onclick="viewDetail('${record.plate_number}')">
                                    <i class="fas fa-eye"></i>
                                </button>
                            </td>
                        </tr>
                    `;
                    tbody.innerHTML += row;
                });
                
                historyOffset += data.records.length;
            } catch (error) {
                console.error('加载历史记录失败:', error);
            }
        }
        
        function loadMoreHistory() {
            loadHistory(false);
        }
        
        // 搜索历史记录
        async function searchHistory() {
            const search = document.getElementById('historySearch').value;
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            
            const params = new URLSearchParams();
            if (search) params.append('plate_number', search);
            if (startDate) params.append('start_date', startDate);
            if (endDate) params.append('end_date', endDate);
            
            try {
                const response = await fetch(`/api/history?${params.toString()}`);
                const data = await response.json();
                
                const tbody = document.getElementById('historyTable');
                tbody.innerHTML = '';
                
                data.records.forEach(record => {
                    const row = `
                        <tr>
                            <td>${record.plate_number}</td>
                            <td>${new Date(record.detection_time).toLocaleString()}</td>
                            <td><span class="badge ${record.confidence > 0.8 ? 'badge-success' : 'badge-warning'}">${(record.confidence * 100).toFixed(1)}%</span></td>
                            <td>${record.province}</td>
                            <td>${record.plate_type}</td>
                            <td>
                                <button class="btn" style="padding: 5px 10px;" onclick="viewDetail('${record.plate_number}')">
                                    <i class="fas fa-eye"></i>
                                </button>
                            </td>
                        </tr>
                    `;
                    tbody.innerHTML += row;
                });
            } catch (error) {
                console.error('搜索失败:', error);
            }
        }
        
        // 导出数据
        async function exportData() {
            try {
                const response = await fetch('/api/export?format=csv');
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `车牌记录_${new Date().toISOString().split('T')[0]}.csv`;
                a.click();
            } catch (error) {
                console.error('导出失败:', error);
            }
        }
        
        // 搜索车牌
        async function searchPlate() {
            const plateNumber = document.getElementById('plateSearch').value;
            if (!plateNumber) {
                alert('请输入车牌号！');
                return;
            }
            
            try {
                const response = await fetch(`/api/search/${plateNumber}`);
                const data = await response.json();
                
                const resultsDiv = document.getElementById('plateSearchResults');
                
                if (data.records.length === 0) {
                    resultsDiv.innerHTML = '<p>未找到相关记录</p>';
                } else {
                    let html = `
                        <div class="card" style="margin-top: 20px;">
                            <h3>车牌: ${data.plate_number}</h3>
                            <p>总访问次数: ${data.total_visits}</p>
                            
                            <h4>进出记录</h4>
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>入场时间</th>
                                        <th>出场时间</th>
                                        <th>停留时长</th>
                                        <th>状态</th>
                                    </tr>
                                </thead>
                                <tbody>
                    `;
                    
                    data.logs.forEach(log => {
                        html += `
                            <tr>
                                <td>${new Date(log.entry_time).toLocaleString()}</td>
                                <td>${log.exit_time ? new Date(log.exit_time).toLocaleString() : '-'}</td>
                                <td>${log.duration_minutes ? log.duration_minutes + '分钟' : '-'}</td>
                                <td><span class="badge ${log.status === 'in_park' ? 'badge-warning' : 'badge-success'}">${log.status === 'in_park' ? '在场' : '已离场'}</span></td>
                            </tr>
                        `;
                    });
                    
                    html += '</tbody></table></div>';
                    resultsDiv.innerHTML = html;
                }
            } catch (error) {
                console.error('搜索失败:', error);
            }
        }
        
        // 查看详情
        function viewDetail(plateNumber) {
            searchPlate();
            document.getElementById('plateSearch').value = plateNumber;
            showTab('search');
        }
        
        // 实时监控
        let monitorInterval = null;
        
        function startRealtimeMonitor() {
            if (monitorInterval) clearInterval(monitorInterval);
            
            updateRealtimeData();
            monitorInterval = setInterval(updateRealtimeData, 5000); // 每5秒更新一次
        }
        
        async function updateRealtimeData() {
            try {
                const response = await fetch('/api/realtime');
                const data = await response.json();
                
                document.getElementById('lastHourCount').textContent = data.last_hour_count;
                
                const tbody = document.getElementById('realtimeTable');
                tbody.innerHTML = '';
                
                data.recent_records.forEach(record => {
                    const row = `
                        <tr>
                            <td>${record.plate_number}</td>
                            <td>${new Date(record.detection_time).toLocaleString()}</td>
                            <td><span class="badge ${record.confidence > 0.8 ? 'badge-success' : 'badge-warning'}">${(record.confidence * 100).toFixed(1)}%</span></td>
                            <td><span class="badge badge-success">新记录</span></td>
                        </tr>
                    `;
                    tbody.innerHTML += row;
                });
            } catch (error) {
                console.error('更新实时数据失败:', error);
            }
        }
        
        // 模态框
        function closeModal() {
            document.getElementById('detailModal').style.display = 'none';
        }
        
        // 加载性能数据
        async function loadPerformance() {
            try {
                const response = await fetch('/api/performance');
                const data = await response.json();
                
                const container = document.getElementById('performanceTables');
                container.innerHTML = '';
                
                // 车辆检测性能表格
                let html = '<h3>🚗 车辆检测性能指标</h3>';
                html += createPerformanceTable(data.vehicle_performance, 
                    ['检测类型', '准确率 (%)', '召回率 (%)', 'F1分数', '平均置信度', '检测速度 (ms)']);
                
                // 车牌识别性能表格
                html += '<h3 style="margin-top: 30px;">🔤 车牌识别性能指标</h3>';
                const plateData = transposeObject(data.plate_performance);
                html += createPerformanceTable(plateData,
                    ['车牌类型', '准确率', '召回率', 'F1分数', '置信度', '速度(ms)']);
                
                // 集成系统性能表格
                html += '<h3 style="margin-top: 30px;">⚡ 集成系统性能指标</h3>';
                html += createPerformanceTable(data.integrated_performance,
                    ['功能模块', '成功率 (%)', '处理时间 (ms)', '内存占用 (MB)', 'GPU使用率 (%)']);
                
                // 性能总结
                html += '<h3 style="margin-top: 30px;">📈 系统性能总结</h3>';
                html += '<div class="stats-grid">';
                
                const summary = data.summary['系统整体性能'];
                for (const [key, value] of Object.entries(summary)) {
                    html += `
                        <div class="stat-card">
                            <div class="label">${key}</div>
                            <div class="value" style="font-size: 24px;">${value}</div>
                        </div>
                    `;
                }
                html += '</div>';
                
                container.innerHTML = html;
            } catch (error) {
                console.error('加载性能数据失败:', error);
            }
        }
        
        function createPerformanceTable(data, headers) {
            let html = '<table class="table">';
            html += '<thead><tr>';
            headers.forEach(header => {
                html += `<th>${header}</th>`;
            });
            html += '</tr></thead><tbody>';
            
            // 获取行数
            const firstKey = Object.keys(data)[0];
            const rowCount = Array.isArray(data[firstKey]) ? data[firstKey].length : 1;
            
            for (let i = 0; i < rowCount; i++) {
                html += '<tr>';
                headers.forEach((header, j) => {
                    const key = Object.keys(data)[j];
                    let value = Array.isArray(data[key]) ? data[key][i] : data[key];
                    
                    // 格式化数值
                    if (typeof value === 'number') {
                        if (header.includes('分数')) {
                            value = value.toFixed(3);
                        } else if (header.includes('%')) {
                            value = value.toFixed(1) + '%';
                        } else if (header.includes('置信度')) {
                            value = value.toFixed(2);
                        } else {
                            value = value.toFixed(1);
                        }
                    }
                    
                    html += `<td>${value}</td>`;
                });
                html += '</tr>';
            }
            
            html += '</tbody></table>';
            return html;
        }
        
        function transposeObject(obj) {
            const result = {};
            const rows = obj[Object.keys(obj)[0]];
            const cols = Object.keys(obj).slice(1);
            
            result['车牌类型'] = cols;
            rows.forEach((row, i) => {
                result[row] = cols.map(col => obj[col][i]);
            });
            
            return result;
        }
        
        function refreshPerformance() {
            loadPerformance();
        }
        
        function downloadPerformanceReport() {
            window.location.href = '/api/export?format=csv';
        }
        
        // 更新时间
        function updateTime() {
            const now = new Date();
            document.getElementById('currentTime').textContent = now.toLocaleString();
        }
        
        setInterval(updateTime, 1000);
        updateTime();
        
        // 页面切换时停止不必要的定时器
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                if (monitorInterval && !btn.textContent.includes('实时监控')) {
                    clearInterval(monitorInterval);
                }
            });
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(ADVANCED_HTML_TEMPLATE)

@app.route('/recognize', methods=['POST'])
def recognize():
    try:
        if 'image' not in request.files:
            return jsonify({'error': '没有上传图片'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400
        
        # 保存上传的文件
        filename = os.path.join(UPLOAD_FOLDER, f"{datetime.now().timestamp()}_{file.filename}")
        file.save(filename)
        
        # 使用集成检测器（同时检测车辆和车牌）
        from integrated_detector import IntegratedDetector
        integrated_detector = IntegratedDetector()
        
        # 执行集成检测
        integrated_results = integrated_detector.process_image(filename)
        
        # 保存车牌到数据库
        for plate in integrated_results['plates']:
            plate['image_path'] = filename
            db.add_record(plate)
        
        # 生成结果图片（包含车辆和车牌框）
        output_path = os.path.join(RESULTS_FOLDER, f'result_{os.path.basename(filename)}')
        result_image, stats = integrated_detector.draw_integrated_results(filename, integrated_results, output_path)
        
        # 转换为base64
        _, buffer = cv2.imencode('.jpg', result_image)
        result_image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        response = {
            'plates': integrated_results['plates'],
            'vehicles': integrated_results['vehicles'],
            'stats': stats,
            'result_image': result_image_base64
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics')
def get_statistics():
    try:
        stats = db.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history')
def get_history():
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        filters = {}
        if request.args.get('plate_number'):
            filters['plate_number'] = request.args.get('plate_number')
        if request.args.get('province'):
            filters['province'] = request.args.get('province')
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        
        history = db.get_history(limit, offset, filters)
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/<plate_number>')
def search_plate(plate_number):
    try:
        result = db.search_plate(plate_number)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export')
def export_data():
    try:
        format = request.args.get('format', 'csv')
        data = db.export_data(format)
        
        if format == 'csv':
            # 添加BOM以支持Excel正确显示中文
            data_with_bom = '\ufeff' + data
            return Response(
                data_with_bom.encode('utf-8-sig'),
                mimetype='text/csv; charset=utf-8',
                headers={'Content-Disposition': f'attachment; filename=plate_records_{datetime.now().strftime("%Y%m%d")}.csv'}
            )
        else:
            return Response(
                data.encode('utf-8'),
                mimetype='application/json; charset=utf-8',
                headers={'Content-Disposition': f'attachment; filename=plate_records_{datetime.now().strftime("%Y%m%d")}.json'}
            )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/realtime')
def get_realtime():
    try:
        data = db.get_real_time_stats()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/performance')
def get_performance():
    """获取系统性能指标"""
    try:
        from detection_metrics import DetectionMetrics
        metrics = DetectionMetrics()
        
        # 获取性能数据
        vehicle_perf, plate_perf, integrated_perf = metrics.generate_performance_table()
        summary = metrics.get_summary_stats()
        
        return jsonify({
            'vehicle_performance': vehicle_perf,
            'plate_performance': plate_perf,
            'integrated_performance': integrated_perf,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)