import sqlite3
import os
from typing import Optional
from base64 import b64encode, b64decode

DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/user_configs.db')

class UserConfigDB:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
            CREATE TABLE IF NOT EXISTS user_configs (
                user_id TEXT PRIMARY KEY,
                student_id TEXT,
                password TEXT,
                area_id TEXT,
                dept_id TEXT,
                floor_id TEXT,
                room_no TEXT,
                dorm_name TEXT,
                weather_report_enabled INTEGER DEFAULT 0,
                weather_report_location TEXT,
                elec_alert_enabled INTEGER DEFAULT 0
            )''')
            # 升级已有表结构，添加新字段（如果不存在）
            try:
                conn.execute('ALTER TABLE user_configs ADD COLUMN dorm_name TEXT')
            except Exception:
                pass
            try:
                conn.execute('ALTER TABLE user_configs ADD COLUMN weather_report_enabled INTEGER DEFAULT 0')
            except Exception:
                pass
            try:
                conn.execute('ALTER TABLE user_configs ADD COLUMN weather_report_location TEXT')
            except Exception:
                pass
            try:
                conn.execute('ALTER TABLE user_configs ADD COLUMN elec_alert_enabled INTEGER DEFAULT 0')
            except Exception:
                pass
            conn.commit()
    def set_weather_report(self, user_id: str, enabled: bool, location: str = None):
        with sqlite3.connect(self.db_path) as conn:
            if enabled:
                conn.execute('''UPDATE user_configs SET weather_report_enabled=1, weather_report_location=? WHERE user_id=?''', (location, user_id))
            else:
                conn.execute('''UPDATE user_configs SET weather_report_enabled=0 WHERE user_id=?''', (user_id,))
            conn.commit()

    def get_weather_report(self, user_id: str):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute('SELECT weather_report_enabled, weather_report_location FROM user_configs WHERE user_id=?', (user_id,))
            row = cur.fetchone()
            if row:
                return bool(row[0]), row[1]
            return False, None

    def set_elec_alert(self, user_id: str, enabled: bool):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''UPDATE user_configs SET elec_alert_enabled=? WHERE user_id=?''', (1 if enabled else 0, user_id))
            conn.commit()

    def get_elec_alert(self, user_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute('SELECT elec_alert_enabled FROM user_configs WHERE user_id=?', (user_id,))
            row = cur.fetchone()
            if row:
                return bool(row[0])
            return False

    def set_auth(self, user_id: str, student_id: str, password: str):
        enc_pwd = b64encode(password.encode()).decode()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''INSERT OR REPLACE INTO user_configs (user_id, student_id, password) VALUES (?, ?, ?)''',
                         (user_id, student_id, enc_pwd))
            conn.commit()

    def get_auth(self, user_id: str) -> Optional[tuple]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute('SELECT student_id, password FROM user_configs WHERE user_id=?', (user_id,))
            row = cur.fetchone()
            if row:
                return row[0], b64decode(row[1]).decode()
            return None

    def set_dorm(self, user_id: str, area_id: str, dept_id: str, floor_id: str, room_no: str, dorm_name: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''UPDATE user_configs SET area_id=?, dept_id=?, floor_id=?, room_no=?, dorm_name=? WHERE user_id=?''',
                         (area_id, dept_id, floor_id, room_no, dorm_name, user_id))
            conn.commit()

    def get_dorm(self, user_id: str) -> Optional[tuple]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute('SELECT area_id, dept_id, floor_id, room_no, dorm_name FROM user_configs WHERE user_id=?', (user_id,))
            row = cur.fetchone()
            if row and all(row[:4]):
                return row
            return None

    def clear_dorm(self, user_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''UPDATE user_configs SET area_id=NULL, dept_id=NULL, floor_id=NULL, room_no=NULL WHERE user_id=?''', (user_id,))
            conn.commit()

user_db = UserConfigDB()
