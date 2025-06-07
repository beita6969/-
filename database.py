import sqlite3
from datetime import datetime
import json
import os

class PlateDatabase:
    def __init__(self, db_path='plate_records.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 车牌识别记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plate_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_number TEXT NOT NULL,
                image_path TEXT,
                detection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confidence REAL,
                detection_confidence REAL,
                ocr_confidence REAL,
                bbox TEXT,
                province TEXT,
                city_code TEXT,
                plate_type TEXT,
                vehicle_type TEXT,
                color TEXT,
                entry_exit TEXT DEFAULT 'unknown'
            )
        ''')
        
        # 车辆进出记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vehicle_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_number TEXT NOT NULL,
                entry_time TIMESTAMP,
                exit_time TIMESTAMP,
                duration_minutes INTEGER,
                status TEXT DEFAULT 'in_park'
            )
        ''')
        
        # 统计信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE DEFAULT CURRENT_DATE,
                total_vehicles INTEGER DEFAULT 0,
                unique_vehicles INTEGER DEFAULT 0,
                avg_confidence REAL DEFAULT 0,
                province_distribution TEXT,
                hour_distribution TEXT
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_plate_number ON plate_records(plate_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_detection_time ON plate_records(detection_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_province ON plate_records(province)')
        
        conn.commit()
        conn.close()
    
    def add_record(self, plate_data):
        """添加识别记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 解析省份
        province = plate_data['plate_text'][0] if plate_data['plate_text'] else ''
        city_code = plate_data['plate_text'][1] if len(plate_data['plate_text']) > 1 else ''
        
        # 判断车牌类型
        plate_type = self._get_plate_type(plate_data['plate_text'])
        
        cursor.execute('''
            INSERT INTO plate_records (
                plate_number, image_path, confidence, 
                detection_confidence, ocr_confidence, bbox,
                province, city_code, plate_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            plate_data['plate_text'],
            plate_data.get('image_path', ''),
            plate_data['overall_confidence'],
            plate_data['detection_confidence'],
            plate_data['ocr_confidence'],
            json.dumps(plate_data['bbox']),
            province,
            city_code,
            plate_type
        ))
        
        record_id = cursor.lastrowid
        
        # 更新车辆进出记录
        self._update_vehicle_log(cursor, plate_data['plate_text'])
        
        conn.commit()
        conn.close()
        
        return record_id
    
    def _get_plate_type(self, plate_number):
        """判断车牌类型"""
        if not plate_number:
            return 'unknown'
        
        if len(plate_number) == 8:
            return 'new_energy'
        elif plate_number[0] in ['使', '领']:
            return 'special'
        else:
            return 'standard'
    
    def _update_vehicle_log(self, cursor, plate_number):
        """更新车辆进出记录"""
        # 查找最新的未出场记录
        cursor.execute('''
            SELECT id, entry_time FROM vehicle_logs 
            WHERE plate_number = ? AND status = 'in_park'
            ORDER BY entry_time DESC LIMIT 1
        ''', (plate_number,))
        
        result = cursor.fetchone()
        
        if result:
            # 车辆出场
            log_id, entry_time = result
            exit_time = datetime.now()
            entry_dt = datetime.fromisoformat(entry_time)
            duration = int((exit_time - entry_dt).total_seconds() / 60)
            
            cursor.execute('''
                UPDATE vehicle_logs 
                SET exit_time = ?, duration_minutes = ?, status = 'exited'
                WHERE id = ?
            ''', (exit_time, duration, log_id))
        else:
            # 车辆入场
            cursor.execute('''
                INSERT INTO vehicle_logs (plate_number, entry_time)
                VALUES (?, ?)
            ''', (plate_number, datetime.now()))
    
    def get_history(self, limit=100, offset=0, filters=None):
        """获取历史记录"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = 'SELECT * FROM plate_records'
        params = []
        
        if filters:
            conditions = []
            if filters.get('plate_number'):
                conditions.append('plate_number LIKE ?')
                params.append(f"%{filters['plate_number']}%")
            if filters.get('province'):
                conditions.append('province = ?')
                params.append(filters['province'])
            if filters.get('start_date'):
                conditions.append('detection_time >= ?')
                params.append(filters['start_date'])
            if filters.get('end_date'):
                conditions.append('detection_time <= ?')
                params.append(filters['end_date'])
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY detection_time DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        records = [dict(row) for row in cursor.fetchall()]
        
        # 解析JSON字段
        for record in records:
            record['bbox'] = json.loads(record['bbox'])
        
        # 获取总数
        count_query = 'SELECT COUNT(*) FROM plate_records'
        if filters and conditions:
            count_query += ' WHERE ' + ' AND '.join(conditions)
            cursor.execute(count_query, params[:-2])
        else:
            cursor.execute(count_query)
        
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'records': records,
            'total': total,
            'limit': limit,
            'offset': offset
        }
    
    def get_statistics(self, date=None):
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if not date:
            date = datetime.now().date()
        
        # 今日统计
        cursor.execute('''
            SELECT 
                COUNT(*) as total_detections,
                COUNT(DISTINCT plate_number) as unique_vehicles,
                AVG(confidence) as avg_confidence
            FROM plate_records
            WHERE DATE(detection_time) = ?
        ''', (date,))
        
        today_stats = dict(cursor.fetchone())
        
        # 省份分布
        cursor.execute('''
            SELECT province, COUNT(*) as count
            FROM plate_records
            WHERE DATE(detection_time) = ? AND province != ''
            GROUP BY province
            ORDER BY count DESC
        ''', (date,))
        
        province_dist = {row['province']: row['count'] for row in cursor.fetchall()}
        
        # 小时分布
        cursor.execute('''
            SELECT strftime('%H', detection_time) as hour, COUNT(*) as count
            FROM plate_records
            WHERE DATE(detection_time) = ?
            GROUP BY hour
            ORDER BY hour
        ''', (date,))
        
        hour_dist = {int(row['hour']): row['count'] for row in cursor.fetchall()}
        
        # 当前在场车辆
        cursor.execute('''
            SELECT COUNT(*) as vehicles_in_park
            FROM vehicle_logs
            WHERE status = 'in_park'
        ''')
        
        vehicles_in_park = cursor.fetchone()['vehicles_in_park']
        
        # 平均停留时间
        cursor.execute('''
            SELECT AVG(duration_minutes) as avg_duration
            FROM vehicle_logs
            WHERE DATE(exit_time) = ? AND duration_minutes IS NOT NULL
        ''', (date,))
        
        avg_duration = cursor.fetchone()['avg_duration'] or 0
        
        # 车牌类型分布
        cursor.execute('''
            SELECT plate_type, COUNT(*) as count
            FROM plate_records
            WHERE DATE(detection_time) = ?
            GROUP BY plate_type
        ''', (date,))
        
        plate_type_dist = {row['plate_type']: row['count'] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'date': str(date),
            'total_detections': today_stats['total_detections'],
            'unique_vehicles': today_stats['unique_vehicles'],
            'avg_confidence': today_stats['avg_confidence'] or 0,
            'vehicles_in_park': vehicles_in_park,
            'avg_duration_minutes': avg_duration,
            'province_distribution': province_dist,
            'hour_distribution': hour_dist,
            'plate_type_distribution': plate_type_dist
        }
    
    def search_plate(self, plate_number):
        """搜索特定车牌"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取所有记录
        cursor.execute('''
            SELECT * FROM plate_records
            WHERE plate_number = ?
            ORDER BY detection_time DESC
        ''', (plate_number,))
        
        records = [dict(row) for row in cursor.fetchall()]
        for record in records:
            record['bbox'] = json.loads(record['bbox'])
        
        # 获取进出记录
        cursor.execute('''
            SELECT * FROM vehicle_logs
            WHERE plate_number = ?
            ORDER BY entry_time DESC
        ''', (plate_number,))
        
        logs = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'plate_number': plate_number,
            'records': records,
            'logs': logs,
            'total_visits': len(logs)
        }
    
    def export_data(self, format='csv', date_range=None):
        """导出数据"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = 'SELECT * FROM plate_records'
        params = []
        
        if date_range:
            query += ' WHERE detection_time BETWEEN ? AND ?'
            params = date_range
        
        query += ' ORDER BY detection_time DESC'
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        conn.close()
        
        if format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            writer.writerow(['车牌号', '检测时间', '置信度', '省份', '城市代码', '车牌类型'])
            
            # 写入数据
            for record in records:
                confidence_str = f"{float(record['confidence']):.2%}" if record['confidence'] else "0.00%"
                writer.writerow([
                    record['plate_number'] or '',
                    record['detection_time'] or '',
                    confidence_str,
                    record['province'] or '',
                    record['city_code'] or '',
                    record['plate_type'] or ''
                ])
            
            return output.getvalue()
        
        elif format == 'json':
            return json.dumps([dict(row) for row in records], ensure_ascii=False, indent=2)
    
    def get_real_time_stats(self):
        """获取实时统计数据"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 最近1小时的检测
        cursor.execute('''
            SELECT COUNT(*) as last_hour_count
            FROM plate_records
            WHERE detection_time >= datetime('now', '-1 hour')
        ''')
        
        last_hour = cursor.fetchone()['last_hour_count']
        
        # 最近10条记录
        cursor.execute('''
            SELECT plate_number, detection_time, confidence
            FROM plate_records
            ORDER BY detection_time DESC
            LIMIT 10
        ''')
        
        recent_records = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'last_hour_count': last_hour,
            'recent_records': recent_records,
            'timestamp': datetime.now().isoformat()
        }