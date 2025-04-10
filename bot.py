# bot.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
)
import random
from datetime import datetime, timedelta
from config import BOT_TOKEN, ADMIN_ID, VERIFICATION_QUESTIONS, POINTS_CONFIG
from database import Database

# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # 保存用户信息
    db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    user_data = db.get_user(user.id)
    
    if user_data and user_data['is_verified']:
        context.bot.send_message(
            chat_id=chat_id,
            text=f"欢迎回来, {user.first_name}!\n\n"
                 f"🔹  您的积分是: {user_data['points']}\n"
                 f"🔹 VIP状态: {'是' if user_data['is_vip'] else '否'}\n\n"
                 f"使用 /query 进行查询\n"
                 f"使用 /points 查看积分\n"
                 f"使用 /help 获取帮助"
        )
    else:
        start_verification(update, context)

def start_verification(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # 随机选择一个验证问题
    question_data = random.choice(VERIFICATION_QUESTIONS)
    question = question_data["question"]
    answer = question_data["answer"]
    
    # 设置验证会话，有效期10分钟
    expiry = datetime.now() + timedelta(minutes=10)
    db.create_verification_session(user.id, question, answer, expiry)
    
    context.bot.send_message(
        chat_id=chat_id,
        text=f"🔐 账号验证\n\n"
             f"请回答以下问题以验证你不是机器人:\n\n"
             f"❓ 问题: {question}\n\n"
             f"你有10分钟时间回答，最多可以尝试3次。"
    )

def handle_verification_answer(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_answer = update.message.text.strip()
    
    session = db.get_verification_session(user.id)
    
    if not session:
        context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ 没有找到验证会话，请使用 /start 重新开始验证。"
        )
        return
    
    if datetime.now() > session['expiry']:
        context.bot.send_message(
            chat_id=chat_id,
            text="⏳ 验证会话已过期，请使用 /start 重新开始验证。"
        )
        db.delete_verification_session(user.id)
        return
    
    if user_answer == session['answer']:
        db.update_verification(user.id, True)
        db.delete_verification_session(user.id)
        
        context.bot.send_message(
            chat_id=chat_id,
            text="✅ 验证成功！\n\n"
                 f"你获得了 {POINTS_CONFIG['register']} 积分作为注册奖励。\n"
                 "现在你可以使用机器人功能了。输入 /help 查看可用命令。"
        )
    else:
        attempts = session['attempts'] + 1
        db.increment_attempts(user.id)
        
        if attempts >= 3:
            context.bot.send_message(
                chat_id=chat_id,
                text="❌ 验证失败次数过多，请使用 /start 重新开始验证。"
            )
            db.delete_verification_session(user.id)
        else:
            remaining = 3 - attempts
            context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ 答案不正确，请再试一次。剩余尝试次数: {remaining}"
            )

def query(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    user_data = db.get_user(user.id)
    
    if not user_data or not user_data['is_verified']:
        context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ 请先完成验证才能使用查询功能。使用 /start 开始验证。"
        )
        return
    
    if len(context.args) == 0:
        context.bot.send_message(
            chat_id=chat_id,
            text="ℹ️ 使用方法: /query <查询内容>"
        )
        return
    
    query_text = ' '.join(context.args)
    
    # 检查积分
    cost = POINTS_CONFIG['vip_query_cost'] if user_data['is_vip'] else POINTS_CONFIG['query_cost']
    
    if user_data['points'] < cost:
        context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ 积分不足！需要 {cost} 积分，你当前有 {user_data['points']} 积分。\n"
                 "使用 /points 查看积分，或联系管理员充值。"
        )
        return
    
    # 扣除积分
    db.add_points(user.id, -cost)
    
    # 记录查询
    db.log_query(user.id, query_text)
    
    # 这里应该是实际的查询逻辑，示例中只是模拟
    context.bot.send_message(
        chat_id=chat_id,
        text=f"🔍 查询结果 (消耗 {cost} 积分):\n\n"
             f"查询内容: {query_text}\n\n"
             "示例结果:\n"
             "用户名: example_user\n"
             "邮箱: example@email.com\n"
             "手机: 138****1234\n\n"
             "剩余积分: {user_data['points'] - cost}"
    )

def points(update: Update, context: CallbackContext):
    user = update.eff