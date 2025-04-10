# config.py
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")          # 从 .env 读取
DATABASE = {
    'host': os.getenv("DB_HOST"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'database': os.getenv("DB_NAME")
}