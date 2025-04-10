# database.py
import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime
from config import DATABASE

class Database:
    def __init__(self):
        self.connection = None
        self.connect()
        self.init_db()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=DATABASE['47.94.98.134'],
                user=DATABASE['SGK'],
                password=DATABASE['SGK'],
                database=DATABASE['SGK']
            )
        except Error as e:
            logging.error(f"数据库连接错误: {e}")
            raise

    def init_db(self):
        try:
            cursor = self.connection.cursor()
            
            # 创建用户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    is_verified BOOLEAN DEFAULT FALSE,
                    points INT DEFAULT 0,
                    is_vip BOOLEAN DEFAULT FALSE,
                    vip_expiry DATE,
                    register_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME
                )
            """)
            
            # 创建查询日志表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT,
                    query_text TEXT,
                    query_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # 创建验证会话表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS verification_sessions (
                    user_id BIGINT PRIMARY KEY,
                    question TEXT,
                    answer TEXT,
                    attempts INT DEFAULT 0,
                    expiry DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            self.connection.commit()
        except Error as e:
            logging.error(f"数据库初始化错误: {e}")
            raise

    def add_user(self, user_id, username, first_name, last_name):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO users (user_id, username, first_name, last_name)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                username = VALUES(username),
                first_name = VALUES(first_name),
                last_name = VALUES(last_name),
                last_login = CURRENT_TIMESTAMP
            """, (user_id, username, first_name, last_name))
            self.connection.commit()
        except Error as e:
            logging.error(f"添加用户错误: {e}")
            raise

    def get_user(self, user_id):
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            return cursor.fetchone()
        except Error as e:
            logging.error(f"获取用户错误: {e}")
            return None

    def update_verification(self, user_id, is_verified):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE users 
                SET is_verified = %s,
                    points = points + %s
                WHERE user_id = %s
            """, (is_verified, POINTS_CONFIG['register'] if is_verified else 0, user_id))
            self.connection.commit()
        except Error as e:
            logging.error(f"更新验证状态错误: {e}")
            raise

    def add_points(self, user_id, points):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE users 
                SET points = points + %s
                WHERE user_id = %s
            """, (points, user_id))
            self.connection.commit()
        except Error as e:
            logging.error(f"添加积分错误: {e}")
            raise

    def set_vip(self, user_id, is_vip, expiry_date=None):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE users 
                SET is_vip = %s,
                    vip_expiry = %s
                WHERE user_id = %s
            """, (is_vip, expiry_date, user_id))
            self.connection.commit()
        except Error as e:
            logging.error(f"设置VIP错误: {e}")
            raise

    def log_query(self, user_id, query_text):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO query_logs (user_id, query_text)
                VALUES (%s, %s)
            """, (user_id, query_text))
            self.connection.comm