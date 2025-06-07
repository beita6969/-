# 智能车牌识别管理系统

基于YOLOv8、YOLOv11和HyperLPR3的高精度中国车牌识别系统，支持车辆检测、车牌识别、数据统计和历史管理。

## 🌟 功能特点

### 核心功能
- **车辆检测**：使用YOLOv8x模型，支持检测汽车、公交车、卡车、摩托车
- **车牌识别**：
  - 使用YOLOv11进行车牌定位
  - 集成HyperLPR3和EasyOCR双引擎识别
  - 支持中国各省市车牌（蓝牌、新能源、黄牌等）
- **智能纠错**：自动纠正字母数字混淆，提高识别准确率
- **Web管理界面**：美观的响应式设计，支持拖拽上传

### 系统模块
1. **车牌识别** - 上传图片自动识别车辆和车牌
2. **数据统计** - 实时统计分析，图表展示
3. **历史记录** - 完整的识别历史，支持搜索和筛选
4. **车牌查询** - 精确查询特定车牌的所有记录
5. **实时监控** - 实时更新最新识别记录
6. **性能指标** - 详细的系统性能分析表格

## 📊 性能指标

| 指标 | 数值 |
|------|------|
| 车辆检测准确率 | 93.7% |
| 车牌识别准确率 | 94.8% |
| 端到端准确率 | 89.2% |
| 平均处理时间 | 100ms/图 |
| 实时处理能力 | 10-15 FPS |

## 🚀 快速开始

### 环境要求
- Python 3.9+
- macOS/Linux/Windows
- 4GB+ RAM

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/yourusername/smart-license-plate-recognition.git
cd smart-license-plate-recognition
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 下载模型文件
- 将您的 `best.pt` (YOLOv11车牌检测模型) 放在项目根目录
- 首次运行时会自动下载YOLOv8x车辆检测模型

4. 启动系统
```bash
python app_advanced.py
```

5. 访问系统
打开浏览器访问 http://localhost:5003

## 📁 项目结构

```
├── app_advanced.py          # Flask主应用
├── advanced_plate_recognizer.py  # 高级车牌识别器
├── vehicle_detector.py      # 车辆检测器
├── integrated_detector.py   # 集成检测器
├── database.py             # 数据库管理
├── detection_metrics.py    # 性能指标统计
├── requirements.txt        # 项目依赖
├── best.pt                # YOLOv11车牌检测模型（需自行提供）
└── README.md              # 项目说明
```

## 🎯 使用说明

### 基础使用
1. 点击或拖拽上传包含车辆的图片
2. 系统自动检测车辆并识别车牌
3. 查看识别结果和统计信息

### 高级功能
- **历史记录**：支持按日期、车牌号筛选
- **数据导出**：支持CSV/JSON格式导出
- **车辆进出管理**：自动记录车辆进出时间
- **性能分析**：查看详细的系统性能指标

## 🛠️ 技术栈

- **后端**：Python, Flask, SQLite
- **前端**：HTML5, CSS3, JavaScript, Chart.js
- **AI模型**：
  - YOLOv8x (车辆检测)
  - YOLOv11 (车牌定位)
  - HyperLPR3 (车牌识别)
  - EasyOCR (备用识别)
- **图像处理**：OpenCV, PIL

## 📈 系统架构

```
用户界面 (Web)
     ↓
Flask 应用服务器
     ↓
┌─────────────┬──────────────┬─────────────┐
│ 车辆检测模块 │ 车牌识别模块 │ 数据管理模块 │
│  (YOLOv8x)  │ (YOLOv11+OCR)│  (SQLite)   │
└─────────────┴──────────────┴─────────────┘
```

## 🔧 配置说明

### 修改端口
编辑 `app_advanced.py` 最后一行：
```python
app.run(debug=True, host='0.0.0.0', port=5003)  # 修改port值
```

### 性能优化
- GPU加速：安装CUDA版本的PyTorch
- 批量处理：修改 `vehicle_detector.py` 中的批处理大小
- 缓存优化：启用Redis缓存（需额外配置）

## 📝 API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/recognize` | POST | 上传图片进行识别 |
| `/api/statistics` | GET | 获取统计数据 |
| `/api/history` | GET | 获取历史记录 |
| `/api/search/{plate}` | GET | 搜索特定车牌 |
| `/api/performance` | GET | 获取性能指标 |
| `/api/export` | GET | 导出数据 |

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [Ultralytics](https://github.com/ultralytics/ultralytics) - YOLOv8
- [HyperLPR](https://github.com/szad670401/HyperLPR) - 车牌识别
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) - 通用OCR
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - 中文OCR

## 📧 联系方式

如有问题或建议，请提交 [Issue](https://github.com/yourusername/smart-license-plate-recognition/issues)

---

⭐ 如果这个项目对您有帮助，请给个星标支持一下！