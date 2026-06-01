#==================== Import ======================#
from colorama import Fore
from pyrogram import Client, filters, idle, errors
from pyrogram.types import *
from bs4 import BeautifulSoup
from functools import wraps, lru_cache
from dbutils.pooled_db import PooledDB
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import subprocess
import threading
import html
import zipfile
import pymysql
import shutil
import signal
import json
import re
import os
import time
import logging
import requests
import hashlib
import random
import string
import ssl
import urllib3
#==================== Config =====================#
Admin = 8103067280
Token = "8783265424:AAFTP5QRCLOXYTmFHI3vYhkV74c3PaDfDQM"
API_ID = 32723346
API_HASH = "00b5473e6d13906442e223145510676e"
Channel_ID = "NexSelf"
Channel_Help = "NexSelf_Help"
Helper_ID = "SHAH_SELF"
DBName = "SELFSAZ"
api_channel = "NexSelf"
DBUser = "SELFSAZ"
DBPass = "Zxcvbnm1111"
HelperDBName = "SELF_SAZ"
HelperDBUser = "SELF_SAZ"
HelperDBPass = "Zxcvbnm1111"
CardNumber = "6037701213986919"
CardName = "امیرعلی میرزایی"
ZARINPAL_DESCRIPTION = "خرید اشتراک دستیار تلگرام"

_settings_cache = {}
_user_cache = {}
_file_cache = {}
_channel_cache = {}
_cache_lock = threading.RLock()
_CACHE_TTL = 30
#==================== Create =====================#
if not os.path.isdir("sessions"):
    os.mkdir("sessions")
if not os.path.isdir("selfs"):
    os.mkdir("selfs")
if not os.path.isdir("cards"):
    os.mkdir("cards")
#===================== App =======================#

logging.getLogger("pyrogram").setLevel(logging.WARNING)

app = Client("Clevear", api_id=API_ID, api_hash=API_HASH, bot_token=Token, workers=200, sleep_threshold=120, max_concurrent_transmissions=100)

temp_Client = {}
lock = asyncio.Lock()

#==================== Database Functions =====================#


db_pool = PooledDB(
    creator=pymysql,
    maxconnections=100,
    mincached=30,
    maxcached=50,
    blocking=False,
    maxusage=2000,
    setsession=[],
    ping=3,
    host="localhost",
    user=DBUser,
    password=DBPass,
    database=DBName,
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor,
    connect_timeout=5,
    read_timeout=20,
    write_timeout=20
)

helper_db_pool = PooledDB(
    creator=pymysql,
    maxconnections=30,
    mincached=10,
    maxcached=20,
    blocking=False,
    host="localhost",
    user=HelperDBUser,
    password=HelperDBPass,
    database=HelperDBName,
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

def _clean_expired_cache():
    current_time = time.time()
    with _cache_lock:
        expired_keys = []
        for key, (value, timestamp) in _user_cache.items():
            if current_time - timestamp > _CACHE_TTL:
                expired_keys.append(key)
                
        for key in expired_keys:
            _user_cache.pop(key, None)
            
        if current_time % 600 < 1:
            expired_files = []
            
            for path, (status, timestamp) in _file_cache.items():
                if current_time - timestamp > 600:
                    expired_files.append(path)
            
            for path in expired_files:
                _file_cache.pop(path, None)

def get_data(query, params=None):
    try:
        connection = pymysql.connect(
            host="localhost",
            user=DBUser,
            password=DBPass,
            database=DBName,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchone()
            
        connection.close()
            
        return result
    except Exception as e:
        return None

def update_data(query, params=None):
    try:
        connection = pymysql.connect(
            host="localhost",
            user=DBUser,
            password=DBPass,
            database=DBName,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            connection.commit()
            affected = cursor.rowcount
            
        connection.close()
        return affected
    except Exception as e:
        return 0
				

@lru_cache(maxsize=1000)
def get_data_cached(query, *params):
    connection = db_pool.connection()
    try:
        with connection.cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()
    finally:
        connection.close()

def get_datas(query, params=None, use_cache=False, cache_key=None):
    if use_cache and cache_key:
        with _cache_lock:
            if cache_key in _user_cache:
                data, timestamp = _user_cache[cache_key]
                if time.time() - timestamp < _CACHE_TTL:
                    return data
    
    connection = db_pool.connection()
    try:
        with connection.cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchall()
            
            if use_cache and cache_key:
                with _cache_lock:
                    _user_cache[cache_key] = (result, time.time())
            
            return result
    finally:
        connection.close()

def helper_getdata(query):
    with pymysql.connect(host="localhost", database=HelperDBName, user=HelperDBUser, password=HelperDBPass) as connect:
        db = connect.cursor()
        db.execute(query)
        result = db.fetchone()
        return result

def helper_updata(query):
    with pymysql.connect(host="localhost", database=HelperDBName, user=HelperDBUser, password=HelperDBPass) as connect:
        db = connect.cursor()
        db.execute(query)
        connect.commit()

def add_card(user_id, card_number, bank_name=None):
    with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass) as connect:
        db = connect.cursor()
        if bank_name:
            db.execute(f"INSERT INTO cards(user_id, card_number, bank_name, verified) VALUES({user_id}, '{card_number}', '{bank_name}', 'pending')")
        else:
            db.execute(f"INSERT INTO cards(user_id, card_number, verified) VALUES({user_id}, '{card_number}', 'pending')")
        connect.commit()

#==================== Optimized Card Functions =====================#

@lru_cache(maxsize=500)
def get_user_cards(user_id, only_verified=True):
    cache_key = f"cards_{user_id}_{only_verified}"
    
    with _cache_lock:
        if cache_key in _user_cache:
            cards, timestamp = _user_cache[cache_key]
            if time.time() - timestamp < 60:
                return cards
    
    # **تغییر مهم: بدون JOIN با user**
    if only_verified:
        query = """
        SELECT c.*
        FROM cards c
        WHERE c.user_id = %s AND c.verified = 'verified'
        ORDER BY c.created_at DESC
        """
    else:
        query = """
        SELECT c.*
        FROM cards c
        WHERE c.user_id = %s
        ORDER BY c.created_at DESC
        """
    
    # استفاده از اتصال مستقیم
    connection = db_pool.connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, [user_id])
            cards = cursor.fetchall()
            
            # ذخیره در کش
            with _cache_lock:
                _user_cache[cache_key] = (cards, time.time())
            
            return cards
    finally:
        connection.close()
		
def get_user_info(user_id):
    try:
        result = get_data(f"SELECT * FROM user WHERE id = {user_id}")
        
        if result:
            user_data = {
                "id": user_id,
                "step": result.get("step", "none"),
                "phone": result.get("phone"),
                "expir": result.get("expir", 0),
                "api_id": result.get("api_id"),
                "api_hash": result.get("api_hash"),
                "account": result.get("account", "unverified"),
                "self": result.get("self", "inactive"),
                "pid": result.get("pid"),
                "last_language_change": result.get("last_language_change")
            }
            return user_data
        
        insert_query = f"""
        INSERT INTO user (id, step, expir, account, self) 
        VALUES ({user_id}, 'none', 0, 'unverified', 'inactive')
        """
        
        if update_data(insert_query) > 0:
            new_result = get_data(f"SELECT * FROM user WHERE id = {user_id}")
            if new_result:
                return {
                    "id": user_id,
                    "step": "none",
                    "phone": None,
                    "expir": 0,
                    "api_id": None,
                    "api_hash": None,
                    "account": "unverified",
                    "self": "inactive",
                    "pid": None,
                    "last_language_change": None
                }
        
        return {"id": user_id, "step": "none", "expir": 0}
        
    except Exception as e:
        return {"id": user_id, "step": "none", "expir": 0}
				

def check_database_connection():
    try:
        connection = pymysql.connect(
            host="localhost",
            user=DBUser,
            password=DBPass,
            database=DBName,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            
            cursor.execute("DESCRIBE user")
        
        connection.close()
        return True
    except Exception as e:
        return False

def ensure_user_exists(user_id):
    try:
        check = get_data("SELECT id FROM user WHERE id = %s", params=[user_id])
        
        if not check:
            update_data("INSERT INTO user(id) VALUES(%s)", params=[user_id])
            invalidate_user_cache(user_id)
            return True
        return True
    except Exception as e:
        return False

def get_user_all_cards(user_id):
    with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass, cursorclass=pymysql.cursors.DictCursor) as connect:
        db = connect.cursor()
        db.execute(f"SELECT * FROM cards WHERE user_id = '{user_id}' ORDER BY id DESC")
        result = db.fetchall()
        return result

def get_pending_cards():
    with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass, cursorclass=pymysql.cursors.DictCursor) as connect:
        db = connect.cursor()
        db.execute("SELECT * FROM cards WHERE verified = 'pending'")
        result = db.fetchall()
        return result

def update_card_status(card_id, status, bank_name=None):
    with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass) as connect:
        db = connect.cursor()
        if bank_name:
            db.execute(f"UPDATE cards SET verified = '{status}', bank_name = '{bank_name}' WHERE id = '{card_id}'")
        else:
            db.execute(f"UPDATE cards SET verified = '{status}' WHERE id = '{card_id}'")
        connect.commit()
    
    # **پاک کردن کش بعد از آپدیت**
    try:
        # پیدا کردن user_id این کارت
        with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass, cursorclass=pymysql.cursors.DictCursor) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT user_id FROM cards WHERE id = '{card_id}'")
            result = cursor.fetchone()
            if result:
                user_id = result['user_id']
                
                # پاک کردن همه کش‌های مربوط به کارت‌های این کاربر
                with _cache_lock:
                    # لیست کلیدهایی که باید پاک شوند
                    keys_to_delete = [key for key in _user_cache.keys() 
                                    if key.startswith(f"cards_{user_id}")]
                    
                    for key in keys_to_delete:
                        del _user_cache[key]
                
                # پاک کردن LRU کش
                get_user_cards.cache_clear()
    except:
        pass
    
    return True

def delete_card(card_id):
    with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass) as connect:
        db = connect.cursor()
        db.execute(f"DELETE FROM cards WHERE id = '{card_id}'")
        connect.commit()

def get_card_by_number(user_id, card_number):
    with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass, cursorclass=pymysql.cursors.DictCursor) as connect:
        db = connect.cursor()
        db.execute(f"SELECT * FROM cards WHERE user_id = '{user_id}' AND card_number = '{card_number}' LIMIT 1")
        result = db.fetchone()
        return result

def get_card_by_id(card_id):
    with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass, cursorclass=pymysql.cursors.DictCursor) as connect:
        db = connect.cursor()
        db.execute(f"SELECT * FROM cards WHERE id = '{card_id}' LIMIT 1")
        result = db.fetchone()
        return result

def generate_random_code(length=16):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def create_code(days):
    code = generate_random_code()
    with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass) as connect:
        db = connect.cursor()
        db.execute(f"INSERT INTO codes(code, days) VALUES('{code}', '{days}')")
        connect.commit()
    return code

def get_code_by_value(code_value):
    with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass, cursorclass=pymysql.cursors.DictCursor) as connect:
        db = connect.cursor()
        db.execute(f"SELECT * FROM codes WHERE code = '{code_value}' AND is_active = TRUE LIMIT 1")
        result = db.fetchone()
        return result

def use_code(code_value, user_id):
    with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass) as connect:
        db = connect.cursor()
        db.execute(f"UPDATE codes SET used_by = '{user_id}', used_at = NOW(), is_active = FALSE WHERE code = '{code_value}'")
        connect.commit()

def get_active_codes():
    with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass, cursorclass=pymysql.cursors.DictCursor) as connect:
        db = connect.cursor()
        db.execute("SELECT * FROM codes WHERE is_active = TRUE ORDER BY created_at DESC")
        result = db.fetchall()
        return result

def get_all_codes():
    with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass, cursorclass=pymysql.cursors.DictCursor) as connect:
        db = connect.cursor()
        db.execute("SELECT * FROM codes ORDER BY created_at DESC")
        result = db.fetchall()
        return result

def delete_code(code_id):
    with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass) as connect:
        db = connect.cursor()
        db.execute(f"DELETE FROM codes WHERE id = '{code_id}'")
        connect.commit()

def cleanup_inactive_codes():
    with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass) as connect:
        db = connect.cursor()
        db.execute("DELETE FROM codes WHERE is_active = FALSE")
        connect.commit()

@lru_cache(maxsize=5000)
def get_user_cached_lru(user_id):
    return get_data("SELECT * FROM user WHERE id = %s", params=[user_id])

def invalidate_user_cache(user_id=None):
    with _cache_lock:
        if user_id:
            keys_to_remove = []
            for key in _user_cache.keys():
                if f"user_{user_id}" in key or f"user_full_{user_id}" in key:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                _user_cache.pop(key, None)
            
            get_user_cached_lru.cache_clear()
        else:
            _user_cache.clear()
            get_user_cached_lru.cache_clear()

#==================== File System Cache =====================#
def check_file_cached(path):
    current_time = time.time()
    
    with _cache_lock:
        if path in _file_cache:
            status, timestamp = _file_cache[path]
            if current_time - timestamp < 10:
                return status
                
    status = os.path.exists(path)
    
    with _cache_lock:
        _file_cache[path] = (status, current_time)
    
    return status

def add_admin(user_id):
    if helper_getdata(f"SELECT * FROM adminlist WHERE id = '{user_id}' LIMIT 1") is None:
        helper_updata(f"INSERT INTO adminlist(id) VALUES({user_id})")

def delete_admin(user_id):
    if helper_getdata(f"SELECT * FROM adminlist WHERE id = '{user_id}' LIMIT 1") is not None:
        helper_updata(f"DELETE FROM adminlist WHERE id = '{user_id}' LIMIT 1")

#================== Database Initialization ===================#

update_data("""
CREATE TABLE IF NOT EXISTS bot(
status varchar(10) DEFAULT 'ON'
) default charset=utf8mb4;
""")

update_data("""
CREATE TABLE IF NOT EXISTS user(
id bigint PRIMARY KEY,
step varchar(150) DEFAULT 'none',
phone varchar(150) DEFAULT NULL,
api_id varchar(50) DEFAULT NULL,
api_hash varchar(100) DEFAULT NULL,
expir bigint DEFAULT '0',
account varchar(50) DEFAULT 'unverified',
self varchar(50) DEFAULT 'inactive',
pid bigint DEFAULT NULL,
last_language_change bigint DEFAULT NULL
) default charset=utf8mb4;
""")

update_data("""
CREATE TABLE IF NOT EXISTS payment_transactions(
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id bigint NOT NULL,
    authority VARCHAR(255) NOT NULL,
    ref_id VARCHAR(255) DEFAULT NULL,
    amount INT NOT NULL,
    plan_days INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_authority (authority),
    INDEX idx_user_status (user_id, status)
) default charset=utf8mb4;
""")

update_data("""
CREATE TABLE IF NOT EXISTS gateway_settings(
    id INT AUTO_INCREMENT PRIMARY KEY,
    gateway_name VARCHAR(50) NOT NULL,
    merchant_id VARCHAR(255) DEFAULT NULL,
    sandbox_mode BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_gateway (gateway_name)
) default charset=utf8mb4;
""")

update_data("""
CREATE TABLE IF NOT EXISTS codes(
id INT AUTO_INCREMENT PRIMARY KEY,
code VARCHAR(20) UNIQUE NOT NULL,
days INT NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
used_by BIGINT DEFAULT NULL,
used_at TIMESTAMP NULL,
is_active BOOLEAN DEFAULT TRUE
) default charset=utf8mb4;
""")

update_data("""
CREATE TABLE IF NOT EXISTS cards(
id INT AUTO_INCREMENT PRIMARY KEY,
user_id bigint NOT NULL,
card_number varchar(20) NOT NULL,
bank_name varchar(50) DEFAULT NULL,
verified varchar(10) DEFAULT 'pending',
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
) default charset=utf8mb4;
""")

update_data("""
CREATE TABLE IF NOT EXISTS settings(
id INT AUTO_INCREMENT PRIMARY KEY,
setting_key VARCHAR(100) NOT NULL UNIQUE,
setting_value TEXT NOT NULL,
description VARCHAR(255) DEFAULT NULL,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) default charset=utf8mb4;
""")

update_data("""
CREATE TABLE IF NOT EXISTS block(
id bigint PRIMARY KEY
) default charset=utf8mb4;
""")

helper_updata("""
CREATE TABLE IF NOT EXISTS ownerlist(
id bigint PRIMARY KEY
) default charset=utf8mb4;
""")

helper_updata("""
CREATE TABLE IF NOT EXISTS adminlist(
id bigint PRIMARY KEY
) default charset=utf8mb4;
""")

bot = get_data("SELECT * FROM bot")
if bot is None:
    update_data("INSERT INTO bot() VALUES()")

OwnerUser = helper_getdata(f"SELECT * FROM ownerlist WHERE id = '{Admin}' LIMIT 1")
if OwnerUser is None:
    helper_updata(f"INSERT INTO ownerlist(id) VALUES({Admin})")

AdminUser = helper_getdata(f"SELECT * FROM adminlist WHERE id = '{Admin}' LIMIT 1")
if AdminUser is None:
    helper_updata(f"INSERT INTO adminlist(id) VALUES({Admin})")

default_gateways = [
    ("zarinpal", None, True, False),
]

for gateway_name, merchant_id, sandbox_mode, is_active in default_gateways:
    if get_data(f"SELECT * FROM gateway_settings WHERE gateway_name = '{gateway_name}'") is None:
        update_data(f"INSERT INTO gateway_settings(gateway_name, merchant_id, sandbox_mode, is_active) VALUES('{gateway_name}', '{merchant_id}', {sandbox_mode}, {is_active})")
        
default_settings = [
    ("start_message", "**\nسلام [ {user_link} ],  به ربات خرید دستیار تلگرام خوش آمدید.\n\nتوی این ربات میتونید از خرید، نصب دستیار بهره ببرید.\n\nلطفا اگر سوالی دارید از بخش پشتیبانی ، با پشتیبان ها در ارتباط باشید یا در گروه پشتیبانی ما عضو شوید.\n\n\n **", "پیام استارت ربات"),
    ("price_message", "**\nنرخ ربات دستیار عبارت است از :\n\n» 1 ماهه : ( `{price_1month}` تومان )\n\n» 2 ماهه : ( `{price_2month}` تومان )\n\n» 3 ماهه : ( `{price_3month}` تومان )\n\n» 4 ماهه : ( `{price_4month}` تومان )\n\n» 5 ماهه : ( `{price_5month}` تومان )\n\n» 6 ماهه : ( `{price_6month}` تومان )\n\n\n(⚠️) توجه داشته باشید که ربات دستیار روی شماره های ایران توصیه میشود و در صورت نصب روی شماره های خارج از کشور، ما مسئولیتی در مورد مسدود شدن اکانت نداریم.\n\n\nدر صورتی که میخواهید به صورت ارزی پرداخت کنید از پشتیبانی درخواست ولت کنید.\n‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌\n‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌‌\n**", "پیام نرخ‌ها"),
    ("whatself_message", "**\nسلف به رباتی گفته میشه که روی اکانت شما نصب میشه و امکانات خاصی رو در اختیارتون میزاره ، لازم به ذکر هست که نصب شدن بر روی اکانت شما به معنی وارد شدن ربات به اکانت شما هست ( به دلیل دستور گرفتن و انجام فعالیت ها )\nاز جمله امکاناتی که در اختیار شما قرار میدهد شامل موارد زیر است:\n\n❈ گذاشتن ساعت با فونت های مختلف بر روی بیو ، اسم\n❈ قابلیت تنظیم حالت خوانده شدن خودکار پیام ها\n❈ تنظیم حالت پاسخ خودکار\n❈ پیام انیمیشنی\n❈ منشی هوشمند\n❈ دریافت پنل و تنظیمات اکانت هوشمند\n❈ دو زبانه بودن دستورات و جواب ها\n❈ تغییر نام و کاور فایل ها\n❈ اعلان پیام ادیت و حذف شده در پیوی\n❈ ذخیره پروفایل های جدید و اعلان حذف پروفایل مخاطبین\n\nو امکاناتی دیگر که میتوانید با مراجعه به بخش راهنما آن ها را ببینید و مطالعه کنید!\n\n❈ لازم به ذکر است که امکاناتی که در بالا گفته شده تنها ذره ای از امکانات سلف میباشد .\n**", "پیام توضیح سلف"),
    ("price_1month", "75000", "قیمت 1 ماهه"),
    ("price_2month", "150000", "قیمت 2 ماهه"),
    ("price_3month", "220000", "قیمت 3 ماهه"),
    ("price_4month", "275000", "قیمت 4 ماهه"),
    ("price_5month", "340000", "قیمت 5 ماهه"),
    ("price_6month", "390000", "قیمت 6 ماهه"),
    ("card_number", CardNumber, "شماره کارت"),
    ("card_name", CardName, "نام صاحب کارت"),
    ("phone_restriction", "enabled", "محدودیت شماره (فقط ایران)"),
]

for key, value, description in default_settings:
    if get_data(f"SELECT * FROM settings WHERE setting_key = '{key}'") is None:
        update_data(f"INSERT INTO settings(setting_key, setting_value, description) VALUES('{key}', '{value}', '{description}')")

def get_gateway_status(gateway_name="zarinpal"):
    result = get_data(f"SELECT * FROM gateway_settings WHERE gateway_name = '{gateway_name}' LIMIT 1")
    
    if result:
        is_active = bool(result["is_active"]) if result["is_active"] is not None else False
        sandbox_mode = bool(result["sandbox_mode"]) if result["sandbox_mode"] is not None else True
        
        return {
            "active": is_active,
            "merchant_id": result["merchant_id"],
            "sandbox": sandbox_mode,
            "gateway_name": result["gateway_name"]
        }
    
    update_data(f"""
    INSERT INTO gateway_settings 
    (gateway_name, merchant_id, sandbox_mode, is_active) 
    VALUES ('{gateway_name}', 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', 1, 0)
    """)
    
    return {
        "active": False,
        "merchant_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        "sandbox": True,
        "gateway_name": gateway_name
    }

def update_gateway_settings(gateway_name, merchant_id, sandbox_mode, is_active):
    sandbox_int = 1 if sandbox_mode else 0
    active_int = 1 if is_active else 0
    
    existing = get_data(f"SELECT * FROM gateway_settings WHERE gateway_name = '{gateway_name}'")
    
    if existing:
        query = f"""
        UPDATE gateway_settings 
        SET merchant_id = '{merchant_id}', 
            sandbox_mode = {sandbox_int}, 
            is_active = {active_int},
            updated_at = NOW()
        WHERE gateway_name = '{gateway_name}'
        """
    else:
        query = f"""
        INSERT INTO gateway_settings 
        (gateway_name, merchant_id, sandbox_mode, is_active, created_at, updated_at)
        VALUES ('{gateway_name}', '{merchant_id}', {sandbox_int}, {active_int}, NOW(), NOW())
        """
    
    update_data(query)
    return True

def checker(func):
    @wraps(func)
    async def wrapper(c, m, *args, **kwargs):
        chat_id = m.chat.id if hasattr(m, "chat") else m.from_user.id
        
        if not ensure_user_exists(chat_id):
            await app.send_message(chat_id, "**خطا در سیستم، لطفا دوباره تلاش کنید.**")
            return
        
        block_cache_key = f"block_{chat_id}"
        with _cache_lock:
            if block_cache_key in _user_cache:
                is_blocked, timestamp = _user_cache[block_cache_key]
                if time.time() - timestamp < _CACHE_TTL:
                    if is_blocked and chat_id != Admin:
                        return
        
        block = get_data("SELECT * FROM block WHERE id = %s", params=[chat_id])
        is_blocked = block is not None
        with _cache_lock:
            _user_cache[block_cache_key] = (is_blocked, time.time())
        
        if is_blocked and chat_id != Admin:
            return
        
        bot_cache_key = "bot_status"
        with _cache_lock:
            if bot_cache_key in _user_cache:
                bot_status, timestamp = _user_cache[bot_cache_key]
                if time.time() - timestamp < _CACHE_TTL:
                    if bot_status == "OFF" and chat_id != Admin:
                        await app.send_message(chat_id, "**ربات موقتاً غیرفعال است.**")
                        return
        
        bot = get_data("SELECT status FROM bot LIMIT 1")
        bot_status = bot["status"] if bot else "ON"
        
        with _cache_lock:
            _user_cache[bot_cache_key] = (bot_status, time.time())
        
        if bot_status == "OFF" and chat_id != Admin:
            await app.send_message(chat_id, "**ربات موقتاً غیرفعال است.**")
            return
        
        if get_data("SELECT id FROM user WHERE id = %s", params=[chat_id]) is None:
            update_data("INSERT INTO user(id) VALUES(%s)", params=[chat_id])
            invalidate_user_cache(chat_id)
        
        return await func(c, m, *args, **kwargs)
    
    return wrapper

def format_expiry_time(expir_days):
    try:
        if expir_days <= 0:
            return "0 روز"
        
        days = int(expir_days)
        hours = int((expir_days - days) * 24)
        
        if hours > 0:
            return f"{days} روز و {hours} ساعت"
        else:
            return f"{days} روز"
    except:
        return f"{int(expir_days)} روز"

async def expirdec(user_id):
    user = get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1")
    user_expir = user["expir"]
    if user_expir > 0:
        user_upexpir = user_expir - 1
        update_data(f"UPDATE user SET expir = '{user_upexpir}' WHERE id = '{user_id}' LIMIT 1")
    else:
        job = scheduler.get_job(str(user_id))
        if job:
            scheduler.remove_job(str(user_id))
        if user_id != Admin:
            delete_admin(user_id)
        if os.path.isdir(f"selfs/self-{user_id}"):
            pid = user["pid"]
            try:
                os.kill(pid, signal.SIGKILL)
            except:
                pass
            await asyncio.sleep(1)
            try:
                shutil.rmtree(f"selfs/self-{user_id}")
            except:
                pass
        if os.path.isfile(f"sessions/{user_id}.session"):
            try:
                async with Client(f"sessions/{user_id}") as user_client:
                    await user_client.log_out()
            except:
                pass
            if os.path.isfile(f"sessions/{user_id}.session"):
                os.remove(f"sessions/{user_id}.session")
        if os.path.isfile(f"sessions/{user_id}.session-journal"):
            os.remove(f"sessions/{user_id}.session-journal")
        await app.send_message(user_id, "**انقضای سلف شما** به پایان رسید، شما میتوانید از بخش **خرید اشتراک**، **سلف خود را تمدید کنید.**")
        update_data(f"UPDATE user SET self = 'inactive' WHERE id = '{user_id}' LIMIT 1")
        update_data(f"UPDATE user SET pid = NULL WHERE id = '{user_id}' LIMIT 1")

async def setscheduler(user_id):
    job = scheduler.get_job(str(user_id))
    if not job:
        scheduler.add_job(expirdec, "interval", hours=24, args=[user_id], id=str(user_id))


async def check_self_status(user_id):
    try:
        user_folder = f"selfs/self-{user_id}"
        if not os.path.isdir(user_folder):
            return {
                "status": "not_installed",
                "message": "سلف شما نصب نشده است.",
                "language": None
            }
        
        data_file = os.path.join(user_folder, "data.json")
        if not os.path.isfile(data_file):
            return {
                "status": "error",
                "message": "تنطیمات سلف نصب نشده است.",
                "language": None
            }
        
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        language = data.get("language", "fa")
        language_text = "فارسی" if language == "fa" else "انگلیسی"
        
        user_data = get_data(f"SELECT pid, self FROM user WHERE id = '{user_id}' LIMIT 1")
        if not user_data:
            return {
                "status": "error",
                "message": "اطلاعات ربات پیدا نشد.",
                "language": language_text
            }
        
        pid = user_data.get("pid")
        self_status = user_data.get("self", "inactive")
        
        if pid:
            try:
                os.kill(pid, 0)
                process_status = "running"
            except OSError:
                process_status = "stopped"
        else:
            process_status = "no_pid"
        
        if self_status == "active" and process_status == "running":
            return {
                "status": "healthy",
                "message": "`دستیار شما موردی نداره و روشن هست.`",
                "language": language_text
            }
        elif self_status == "active" and process_status == "stopped":
            return {
                "status": "problem",
                "message": "`دستیار شما با مشکل مواجه شده و نیاز به ورود مجدد است.`",
                "language": language_text
            }
        elif self_status == "inactive":
            return {
                "status": "inactive",
                "message": "`دستیار شما خاموش است.`",
                "language": language_text
            }
        else:
            return {
                "status": "unknown",
                "message": "`وضعیت دستیار شما نامشخص است`",
                "language": language_text
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"**سلف شما نصب نشده است، ابتدا دستیار خود را نصب کنید.**",
            "language": None
        }

async def change_self_language(user_id, target_language):
    try:
        user_folder = f"selfs/self-{user_id}"
        data_file = os.path.join(user_folder, "data.json")
        
        if not os.path.isfile(data_file):
            return False, "**تنظیمات ربات دستیار نصب نشده است.**"
        
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        old_language = data.get("language", "fa")
        
        data["language"] = target_language
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        current_time = int(time.time())
        update_data(f"UPDATE user SET last_language_change = '{current_time}' WHERE id = '{user_id}'")
        
        return True, old_language
        
    except Exception as e:
        return False, str(e)

def can_change_language(user_id):
    user_data = get_data(f"SELECT last_language_change FROM user WHERE id = '{user_id}' LIMIT 1")
    
    if not user_data or user_data.get("last_language_change") is None:
        return True, 0
    
    last_change = int(user_data.get("last_language_change", 0))
    current_time = int(time.time())
    time_passed = current_time - last_change
    
    if time_passed >= 1800:
        return True, 0
    
    remaining_seconds = 1800 - time_passed
    remaining_minutes = (remaining_seconds + 59) // 60
    
    return False, remaining_minutes

def get_current_language(user_id):
    try:
        user_folder = f"selfs/self-{user_id}"
        data_file = os.path.join(user_folder, "data.json")
        
        if not os.path.isfile(data_file):
            return "fa"
        
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get("language", "fa")
    except:
        return "fa"


async def extract_self_files(user_id, language="fa"):
    try:
        user_folder = f"selfs/self-{user_id}"
        
        if os.path.exists(user_folder):
            shutil.rmtree(user_folder)
        
        os.makedirs(user_folder, exist_ok=True)
        
        data_file = os.path.join(user_folder, "data.json")
        default_data = {
            "language": language,
            "user_id": user_id,
            "bot_language": language
        }
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)
        
        zip_path = "source/Self.zip"
        
        if not os.path.isfile(zip_path):
            await app.send_message(user_id, f"**• فایل Self.zip در مسیر {zip_path} یافت نشد.**")
            return False
        
        file_size = os.path.getsize(zip_path)
        if file_size == 0:
            await app.send_message(user_id, "**• فایل Self.zip خالی یا آسیب دیده است.**")
            return False
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                if zip_ref.testzip() is not None:
                    await app.send_message(user_id, "**• فایل Self.zip آسیب دیده است.**")
                    return False
                
                file_list = zip_ref.namelist()
                
                if not file_list:
                    await app.send_message(user_id, "**• فایل Self.zip خالی است.**")
                    return False
                
                zip_ref.extractall(user_folder)
                
                if "self.py" not in file_list:
                    await app.send_message(user_id, f"**• فایل self.py در آرشیو یافت نشد. فایل‌های موجود: {file_list}**")
                    return False
                
                if not os.path.exists(data_file):
                    default_data = {
                        "language": language,
                        "user_id": user_id,
                        "bot_language": language
                    }
                    with open(data_file, 'w', encoding='utf-8') as f:
                        json.dump(default_data, f, ensure_ascii=False, indent=2)
                return True
                
        except zipfile.BadZipFile:
            await app.send_message(user_id, "**• فایل Self.zip معتبر نیست.**")
            return False
            
    except PermissionError as e:
        await app.send_message(user_id, "**• خطای دسترسی: امکان نوشتن در پوشه وجود ندارد.**")
        return False
    except Exception as e:
        error_msg = f"**• خطا در استخراج فایل:**\n```\n{str(e)}\n```"
        await app.send_message(user_id, error_msg)
        return False

def validate_phone_number(phone_number):
    restriction = get_setting("phone_restriction", "disabled")
    
    if restriction == "disabled":
        return True, None
    
    if not phone_number.startswith("+"):
        phone_number = f"+{phone_number}"
    
    if phone_number.startswith("+98"):
        return True, None
    else:
        return False, "**تا اطلاع ثانوی، نصب یا خرید ربات سلف روی اکانت مجازی غیرمجاز میباشد.**"

async def safe_edit_message(chat_id, message_id, new_text):
    try:
        try:
            current_msg = await app.get_messages(chat_id, message_id)
            if current_msg.text == new_text:
                return current_msg, False
        except:
            pass
        
        await app.edit_message_text(chat_id, message_id, new_text)
        
        edited_msg = await app.get_messages(chat_id, message_id)
        return edited_msg, True
    except errors.MessageNotModified:
        try:
            current_msg = await app.get_messages(chat_id, message_id)
            return current_msg, False
        except:
            return None, False
    except Exception as e:
        return None, False

async def start_self_installation(user_id, phone, api_id, api_hash, message_id=None, language="fa"):
    try:
        is_valid, error_message = validate_phone_number(phone)
        if not is_valid:
            if message_id:
                await safe_edit_message(user_id, message_id, "**• نصب ربات سلف روی اکانت مجازی غیرمجاز است.**")
            else:
                await app.send_message(user_id, "**• نصب ربات سلف روی اکانت مجازی غیرمجاز است.**")
            return False
        
        if message_id:
            msg, edited = await safe_edit_message(user_id, message_id, "**• درحال ساخت سلف، لطفا صبور باشید.**")
            if not msg:
                msg = await app.get_messages(user_id, message_id)
        else:
            msg = await app.send_message(user_id, "**• درحال ساخت سلف، لطفا صبور باشید.**")
        
        success = await extract_self_files(user_id, language)
        
        if not success:
            await safe_edit_message(user_id, msg.id, "**استخراج فایل ربات با خطا مواجه شد، با پشتیبانی در ارتباط باشید.**")
            return False
        
        client = Client(
            f"sessions/{user_id}",
            api_id=int(api_id),
            api_hash=api_hash
        )
        
        await client.connect()
        
        sent_code = await client.send_code(phone)
        
        temp_Client[user_id] = {
            "client": client,
            "phone_code_hash": sent_code.phone_code_hash,
            "phone": phone,
            "api_id": api_id,
            "api_hash": api_hash,
            "language": language
        }
        
        caption = "**• با توجه به ویدئو، کدی که از سمت تلگرام برای شما ارسال شده را با استفاده از دکمه زیر به اشتراک بگذارید.**"
        await app.send_animation(
            chat_id=user_id,
            animation="training.gif",
            caption=caption,
            reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="اشتراک گذاری کد", 
                    switch_inline_query_current_chat=""
                )
            ]
        ]))
        
        update_data(f"UPDATE user SET step = 'install_code-{phone}-{api_id}-{api_hash}-{language}' WHERE id = '{user_id}'")
        
        return True
        
    except errors.PhoneNumberInvalid:
        if message_id:
            await safe_edit_message(user_id, message_id, "**• شماره تلفن نامعتبر است.**")
        return False
    except errors.PhoneNumberBanned:
        if message_id:
            await safe_edit_message(user_id, message_id, "**• شماره تلفن مسدود شده است.**")
        return False
    except errors.PhoneNumberFlood:
        if message_id:
            await safe_edit_message(user_id, message_id, "**• درحالت انتضار هستید، منتظر بمانید.**")
        return False
    except Exception as e:
        error_msg = f"**• خطا در نصب سلف:**\n```\n{str(e)[:200]}\n```"
        if message_id:
            await safe_edit_message(user_id, message_id, error_msg)
        else:
            await app.send_message(user_id, error_msg)
        return False

async def verify_code_and_login(user_id, phone, api_id, api_hash, code, language="fa"):
    try:
        if user_id not in temp_Client:
            await app.send_message(user_id, "**• عملیات منقضی شده، مجدد مراحل نصب را انجام دهید.**")
            return
        
        client_data = temp_Client[user_id]
        client = client_data["client"]
        phone_code_hash = client_data["phone_code_hash"]
        stored_language = client_data.get("language", "fa")
        
        try:
            await client.sign_in(
                phone_number=phone,
                phone_code_hash=phone_code_hash,
                phone_code=code
            )
            
        except errors.SessionPasswordNeeded:
            await app.send_message(user_id,
                "**• لطفا رمز دومرحله ای اکانت را بدون هیچ کلمه یا کاراکتر اضافه ای ارسال کنید :**")
            
            update_data(f"UPDATE user SET step = 'install_2fa-{phone}-{api_id}-{api_hash}-{stored_language}' WHERE id = '{user_id}'")
            return
        
        await app.send_message(user_id, "**• ورود به اکانت با موفقیت انجام شد، درحال نصب نهایی سلف، لطفا صبور باشید.**")
        
        try:
            if client.is_connected:
                await client.disconnect()
        except:
            pass
        
        if user_id in temp_Client:
            del temp_Client[user_id]
        
        await asyncio.sleep(3)
        
        await start_self_bot(user_id, api_id, api_hash, None, stored_language)
        
    except errors.PhoneCodeInvalid:
        await app.send_message(user_id, "**• کد وارد شده نامعتبر است، مجدد کد را وارد کنید.**")
    except errors.PhoneCodeExpired:
        await app.send_message(user_id, "**• کد موردنظر باطل شده بود، مجدد عملیات رو آغاز کنید.**")
    except Exception as e:
        await app.send_message(user_id, f"**• خطا در تایید کد، با پشتیبانی در ارتباط باشید.**")

async def verify_2fa_password(user_id, phone, api_id, api_hash, password, language="fa"):
    try:
        
        client = Client(
            f"sessions/{user_id}",
            api_id=int(api_id),
            api_hash=api_hash
        )
        
        await client.connect()
        
        await client.check_password(password)
        
        await app.edit_message_text(user_id, "**• ورود به اکانت با موفقیت انجام شد، درحال نصب نهایی سلف، لطفا صبور باشید.**")
        
        await start_self_bot(user_id, api_id, api_hash, None, language)
        
        await client.disconnect()
        
    except Exception as e:
        await app.send_message(user_id, "**• خطا در تایید رمز، با پشتیانی در ارتباط باشید.**")

async def start_self_bot(user_id, api_id, api_hash, message_id=None, language="fa"):
    try:
        user_folder = f"selfs/self-{user_id}"
        
        async with lock:
            if user_id in temp_Client:
                try:
                    client_data = temp_Client[user_id]
                    if client_data["client"].is_connected:
                        await client_data["client"].disconnect()
                except:
                    pass
                finally:
                    if user_id in temp_Client:
                        del temp_Client[user_id]
        
        user_info = get_data(f"SELECT expir, phone FROM user WHERE id = '{user_id}' LIMIT 1")
        if not user_info:
            if message_id:
                await app.edit_message_text(user_id, message_id, "**• اطلاعات کاربر یافت نشد.**")
            else:
                await app.send_message(user_id, "**• اطلاعات کاربر یافت نشد.**")
            return False

        expir_days = user_info.get("expir", 0)
        phone_number = user_info.get("phone", "ندارد")

        try:
            tg_user = await app.get_users(user_id)
            first_name = html.escape(tg_user.first_name or "ندارد")
            last_name = html.escape(tg_user.last_name or "ندارد")
            username = f"@{tg_user.username}" if tg_user.username else "ندارد"
            user_link = f'<a href="tg://user?id={user_id}">{first_name} {last_name}</a>'
        except:
            first_name = "نامشخص"
            last_name = ""
            username = "ندارد"
            user_link = f"آیدی: {user_id}"
        
        def cleanup_locked_files():
            base_path = f"/home/amyeyenn/public_html/sessions/{user_id}"
            files_to_remove = [
                f"{base_path}.session-journal",
                f"{base_path}.session-wal", 
                f"{base_path}.session-shm",
                f"sessions/{user_id}.session-journal",
                f"sessions/{user_id}.session-wal",
                f"sessions/{user_id}.session-shm"
            ]
            
            removed = []
            for file_path in files_to_remove:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        removed.append(os.path.basename(file_path))
                    except Exception as e:
                        pass
            
            return removed
        
        await asyncio.sleep(3)
        
        if not os.path.isdir(user_folder):
            if message_id:
                await app.edit_message_text(user_id, message_id, "**• عملیات دچار مشکل شد!**")
            else:
                await app.send_message(user_id, "**• عملیات دچار مشکل شد!**")
            return False
        
        self_py_path = os.path.join(user_folder, "self.py")
        if not os.path.exists(self_py_path):
            if message_id:
                await app.edit_message_text(user_id, message_id, "**• فایل پیدا نشد، با پشتیبانی در ارتباط باشید.**")
            else:
                await app.send_message(user_id, "**• فایل پیدا نشد، با پشتیبانی در ارتباط باشید.**")
            return False
        
        log_file = os.path.join(user_folder, f"self_{user_id}_{int(time.time())}.log")
        
        process = subprocess.Popen(
            ["python3", "self.py", str(user_id), str(api_id), api_hash, Helper_ID],
            cwd=user_folder,
            stdout=open(log_file, 'w'),
            stderr=subprocess.STDOUT,
            text=True
        )
        
        await asyncio.sleep(5)
        
        return_code = process.poll()
        
        if return_code is not None:
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                
                if message_id:
                    await app.edit_message_text(user_id, message_id, "**• عملیات کنسل شد، با پشتیبانی در ارتباط باشید.**")
                else:
                    await app.send_message(user_id, "**• عملیات کنسل شد، با پشتیبانی در ارتباط باشید.**")
                
                await app.send_message(Admin,
                    f"**• عملیات نصب سلف برای کاربر [ {user_id} ] با خطا مواجه شد :** ```\n{log_content[:1500]}\n```")
                
            else:
                await app.send_message(Admin, f"**• خطا در نصب ربات کاربر [ {user_id} ]\n• لاگ نصب ثبت نشده است.**")
            
            return False
        
        await asyncio.sleep(10)
        
        return_code = process.poll()
        
        if return_code is None:
            pid = process.pid
            
            update_data(f"UPDATE user SET self = 'active' WHERE id = '{user_id}'")
            update_data(f"UPDATE user SET pid = '{pid}' WHERE id = '{user_id}'")
            
            add_admin(user_id)
            
            await setscheduler(user_id)
            
            if language == "fa":
                help_command = "راهنما"
            else:
                help_command = "HELP"
            
            success_message = f"""**• سلف شما نصب و روشن شد.
با دستور [ `{help_command}` ] میتونید راهنمای سلف رو دریافت کنید.

لطفا بعد نصب سلف حتما اگر رمز دومرحله ای فعال دارید اون رو عوض کنید و یا اکر رمز دومرحله ای روی اکانتتون فعال ندارید، فعال کنید و حواستون باشه فراموشش نکنید.

در صورتی که جوابی دریافت نمیکنید یک دقیقه صبر کنید و بعد دستور بدید، و اکر باز هم جوابی نگرفتید از منوی اصلی به بخش پشتیبانی مراجعه کنید و موضوع رو اطلاع بدید.**"""
            
            if message_id:
                await app.edit_message_text(user_id, message_id, success_message)
            else:
                await app.send_message(user_id, success_message)
            
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    last_lines = lines[-10:] if len(lines) > 10 else lines
                    log_preview = "".join(last_lines)
              
            await app.send_message(Admin, f"**• خرید #اشتراک :\n• نام : [ {first_name} ]\n• یوزرنیم : [ {username} ]\n• آیدی عددی : [ `{user_id}` ]\n• شماره : [ `{phone_number}` ]\n• انقضا : [ `{expir_days}` ]\n• PID : [ `{pid}` ]\n• Api ID : [ `{api_id}` ]\n• Api Hash : [ `{api_hash}` ]\n• زبان : [ `{language}` ]\n ‌ ‌ ‌‌‌‌‌‌‌\n ‌ ‌ ‌**")
            
            await asyncio.sleep(15)
            
            return True
        else:
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                
                if message_id:
                    await app.edit_message_text(user_id, message_id, "**• عملیات کنسل شد، با پشتیبانی در ارتباط باشید.**")
                else:
                    await app.send_message(user_id, "**• عملیات کنسل شد، با پشتیبانی در ارتباط باشید.**")
                return False
            
    except subprocess.TimeoutExpired:
        if message_id:
            await app.edit_message_text(user_id, message_id, "**• خطا، با پشتیبانی در ارتباط باشید.**")
        else:
            await app.send_message(user_id, "**• خطا، با پشتیبانی در ارتباط باشید.**")
        return False
        
    except Exception as e:
        error_msg = f"**• عملیات کنسل شد، با پشتیبانی در ارتباط باشید.**"
        if message_id:
            await app.edit_message_text(user_id, message_id, error_msg)
        else:
            await app.send_message(user_id, error_msg)
        return False
				
def detect_bank(card_number):
    prefix = card_number[:6]
    
    if prefix == "627412":
        return "اقتصاد نوین"
    elif prefix == "207177":
        return "توسعه صادرات ایران"
    elif prefix == "627381":
        return "انصار"
    elif prefix == "502229":
        return "پاسارگاد"
    elif prefix == "505785":
        return "ایران زمین"
    elif prefix == "502806":
        return "شهر"
    elif prefix == "622106":
        return "پارسیان"
    elif prefix == "502908":
        return "توسعه تعاون"
    elif prefix == "639194":
        return "پارسیان"
    elif prefix == "502910":
        return "کارآفرین"
    elif prefix == "627884":
        return "پارسیان"
    elif prefix == "502938":
        return "دی"
    elif prefix == "639347":
        return "پاسارگاد"
    elif prefix == "505416":
        return "گردشگری"
    elif prefix == "502229":
        return "پاسارگاد"
    elif prefix == "505785":
        return "ایران زمین"
    elif prefix == "636214":
        return "آینده"
    elif prefix == "505801":
        return "موسسه اعتباری کوثر (سپه)"
    elif prefix == "627353":
        return "تجارت"
    elif prefix == "589210":
        return "سپه"
    elif prefix == "502908":
        return "توسعه تعاون"
    elif prefix == "589463":
        return "رفاه کارگران"
    elif prefix == "627648":
        return "توسعه صادرات ایران"
    elif prefix == "603769":
        return "صادرات ایران"
    elif prefix == "207177":
        return "توسعه صادرات ایران"
    elif prefix == "603770":
        return "کشاورزی"
    elif prefix == "636949":
        return "حکمت ایرانیان (سپه)"
    elif prefix == "603799":
        return "ملی ایران"
    elif prefix == "502938":
        return "دی"
    elif prefix == "606373":
        return "قرض الحسنه مهر ایران"
    elif prefix == "589463":
        return "رفاه کارگران"
    elif prefix == "610433":
        return "ملت"
    elif prefix == "621986":
        return "سامان"
    elif prefix == "621986":
        return "سامان"
    elif prefix == "589210":
        return "سپه"
    elif prefix == "622106":
        return "پارسیان"
    elif prefix == "639607":
        return "سرمایه"
    elif prefix == "627353":
        return "تجارت"
    elif prefix == "639346":
        return "سینا"
    elif prefix == "627381":
        return "انصار (سپه)"
    elif prefix == "502806":
        return "شهر"
    elif prefix == "627412":
        return "اقتصاد نوین"
    elif prefix == "603769":
        return "صادرات ایران"
    elif prefix == "627488":
        return "کارآفرین"
    elif prefix == "627961":
        return "صنعت و معدن"
    elif prefix == "627648":
        return "توسعه صادرات ایران"
    elif prefix == "606373":
        return "قرض الحسنه مهر ایران"
    elif prefix == "627760":
        return "پست ایران"
    elif prefix == "639599":
        return "قوامین"
    elif prefix == "627884":
        return "پارسیان"
    elif prefix == "627488":
        return "کارآفرین"
    elif prefix == "627961":
        return "صنعت و معدن"
    elif prefix == "502910":
        return "کارآفرین"
    elif prefix == "628023":
        return "مسکن"
    elif prefix == "603770":
        return "کشاورزی"
    elif prefix == "628157":
        return "موسسه اعتباری توسعه"
    elif prefix == "639217":
        return "کشاورزی"
    elif prefix == "636214":
        return "آینده"
    elif prefix == "505416":
        return "گردشگری"
    elif prefix == "636795":
        return "مرکزی"
    elif prefix == "636795":
        return "مرکزی"
    elif prefix == "636949":
        return "حکمت ایرانیان (سپه)"
    elif prefix == "628023":
        return "مسکن"
    elif prefix == "639194":
        return "پارسیان"
    elif prefix == "610433":
        return "ملت"
    elif prefix == "639217":
        return "کشاورزی"
    elif prefix == "991975":
        return "ملت"
    elif prefix == "639346":
        return "سینا"
    elif prefix == "603799":
        return "ملی ایران"
    elif prefix == "639347":
        return "پاسارگاد"
    elif prefix == "639370":
        return "مهر اقتصاد (سپه)"
    elif prefix == "639370":
        return "مهر اقتصاد (سپه)"
    elif prefix == "627760":
        return "پست ایران"
    elif prefix == "639599":
        return "قوامین (سپه)"
    elif prefix == "628157":
        return "موسسه اعتباری توسعه"
    elif prefix == "639607":
        return "سرمایه"
    elif prefix == "505801":
        return "موسسه اعتباری کوثر (سپه)"
    else:
        return "نامشخص"

#==================== Telegram API Auto Functions =====================#

class TelegramAPIAuto:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,fa;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
        })
        self.base_url = "https://my.telegram.org"
        
    def send_phone(self, phone_number):
        try:
            auth_url = f"{self.base_url}/auth"
            response = self.session.get(auth_url, timeout=10)
            
            if response.status_code != 200:
                return {"success": False, "message": f"خطا در دسترسی به سایت: {response.status_code}"}
            
            send_url = f"{self.base_url}/auth/send_password"
            headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': auth_url,
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Accept': 'application/json, text/javascript, */*; q=0.01'
            }
            
            data = {
                'phone': phone_number
            }
            
            response = self.session.post(send_url, data=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if 'random_hash' in result:
                        return {
                            "success": True,
                            "random_hash": result['random_hash'],
                            "message": "کد تأیید ارسال شد"
                        }
                    else:
                        return {"success": False, "message": "پاسخ نامعتبر از سرور"}
                except:
                    return {"success": False, "message": "پاسخ JSON نامعتبر"}
            else:
                return {"success": False, "message": f"خطای HTTP: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "message": f"خطا: {str(e)[:100]}"}
    
    def verify_code(self, phone_number, random_hash, code):
        try:
            login_url = f"{self.base_url}/auth/login"
            headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f"{self.base_url}/auth",
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Accept': 'application/json, text/javascript, */*; q=0.01'
            }
            
            data = {
                'phone': phone_number,
                'random_hash': random_hash,
                'password': code,
                'remember': '1'
            }
            
            response = self.session.post(login_url, data=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if 'error' in result:
                        return {"success": False, "message": result['error']}
                    else:
                        return {"success": True, "message": "ورود موفق"}
                except:
                    return {"success": True, "message": "ورود موفق"}
            else:
                return {"success": False, "message": f"خطای HTTP: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "message": f"خطا: {str(e)[:100]}"}
    
    def get_api_credentials(self):
        try:
            home_url = self.base_url
            response = self.session.get(home_url, timeout=10)
            
            if response.status_code != 200:
                return {"success": False, "message": f"خطا در دسترسی به صفحه اصلی: {response.status_code}"}
            
            if 'Log out' in response.text:
                apps_url = f"{self.base_url}/apps"
                response = self.session.get(apps_url, timeout=10)
                
                if response.status_code == 200:
                    return self.parse_apps_page(response.text)
                else:
                    return {"success": False, "message": f"خطا در دسترسی به صفحه apps: {response.status_code}"}
            else:
                return {"success": False, "message": "لاگین نشده‌اید"}
                
        except Exception as e:
            return {"success": False, "message": f"خطا: {str(e)[:100]}"}
    
    def parse_apps_page(self, html_content):
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            api_text = soup.get_text()
            api_id_match = re.search(r'api_id[\s:]+(\d+)', api_text, re.IGNORECASE)
            api_id = api_id_match.group(1) if api_id_match else None
            api_hash_match = re.search(r'api_hash[\s:]+([a-f0-9]{32})', api_text, re.IGNORECASE)
            api_hash = api_hash_match.group(1) if api_hash_match else None
            
            if api_id and api_hash:
                return {
                    "success": True,
                    "api_id": api_id,
                    "api_hash": api_hash,
                    "message": "API اطلاعات دریافت شد"
                }
            else:
                create_form = soup.find('form', {'action': '/apps/create'})
                
                if create_form:
                    csrf_input = create_form.find('input', {'name': 'csrfmiddlewaretoken'})
                    
                    if csrf_input and csrf_input.get('value'):
                        return self.create_new_application(csrf_input.get('value'))
                    else:
                        csrf_pattern = r"csrf_token\s*:\s*['\"]([^'\"]+)['\"]"
                        match = re.search(csrf_pattern, html_content)
                        
                        if match:
                            return self.create_new_application(match.group(1))
                        else:
                            return {"success": False, "message": "CSRF token یافت نشد"}
                else:
                    return {"success": False, "message": "فرم ایجاد اپلیکیشن یافت نشد"}
                
        except Exception as e:
            return {"success": False, "message": f"خطا در پارس کردن صفحه: {str(e)[:100]}"}
    
    def create_new_application(self, csrf_token):
        try:
            create_url = f"{self.base_url}/apps/create"
            
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            app_title = f"Telegram Self Bot {random_suffix}"
            short_name = f"selfbot{random_suffix}"
            
            data = {
                'csrfmiddlewaretoken': csrf_token,
                'app_title': app_title,
                'app_shortname': short_name,
                'app_url': 'https://telegram.org',
                'app_platform': 'android',
                'app_desc': 'Telegram Self Bot Assistant'
            }
            
            headers = {
                'Referer': f"{self.base_url}/apps",
                'Origin': self.base_url,
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            
            response = self.session.post(create_url, data=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                apps_url = f"{self.base_url}/apps"
                response = self.session.get(apps_url, timeout=10)
                
                if response.status_code == 200:
                    return self.parse_apps_page(response.text)
                else:
                    return {"success": False, "message": f"خطا در بازگشت به صفحه apps: {response.status_code}"}
            else:
                return {"success": False, "message": f"خطا در ایجاد اپلیکیشن: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "message": f"خطا در ایجاد اپلیکیشن: {str(e)[:100]}"}

async def confirm_auto_api_code(user_id, message_id, code, is_confirmed=False):
    try:
        if not is_confirmed:
            await app.send_message(
                user_id,
                f"**» کد ارسالی شما ذخیره شد.\n\n❁ آیا کد ( {code} ) را تایید میکنید؟\n❁ در صورت اشتباه بودن کد ، لطفا کد صحیح را ارسال کنید، در غیر این صورت از دکمه بله استفاده کنید.**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("بله (✅)", callback_data=f"ConfirmCode-{code}")]
                ])
            )
        else:
            user_info = get_data(f"SELECT phone FROM user WHERE id = '{user_id}' LIMIT 1")
            
            await app.edit_message_text(user_id, message_id, "**• بسیار خوب، کد ارسالی شما ذخیره شد، لطفا منتظر بمانید.**")
            
            await asyncio.sleep(2)
            result = await process_auto_api(user_id, user_info["phone"], code)
                
            if result["success"]:
                await app.send_message(
                    user_id,
                    "**• عملیات به پایان رسید و Api Id, Api Hash برای اکانت شما ساخته شد و اطلاعات شما ذخیره شد ، برای ادامه روی دکمه زیر کلیک کنید.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("• ادامه •", callback_data=f"ShowAPIDetails-{code}")]
                    ])
                )
                    
                update_data(f"""UPDATE user SET step = 'api_received-{result.get('api_id', '')}-{result.get('api_hash', '')}-{code}' WHERE id = '{user_id}' """)
            else:
                await app.edit_message_text(
                    user_id, message_id,
                    f"**خطا :**"
                    f"\n```\n{result['message']}\n```",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("(🔙) بازگشت", callback_data="InstallSelf")]
                    ])
                )
    except Exception as e:
        pass

telegram_sessions = {}

async def process_auto_api(user_id, phone_number, code=None):
    try:
        if user_id not in telegram_sessions:
            telegram_api = TelegramAPIAuto()
            send_result = telegram_api.send_phone(phone_number)
            
            if not send_result["success"]:
                return send_result
            
            telegram_sessions[user_id] = {
                "api": telegram_api,
                "phone": phone_number,
                "random_hash": send_result["random_hash"],
                "timestamp": time.time()
            }
            
            return {
                "success": True,
                "message": "کد تأیید ارسال شد",
                "requires_code": True
            }
        else:
            session_data = telegram_sessions[user_id]
            telegram_api = session_data["api"]
            
            if not code:
                return {"success": False, "message": "کد تأیید مورد نیاز است"}
            
            verify_result = telegram_api.verify_code(
                session_data["phone"],
                session_data["random_hash"],
                code
            )
            
            if not verify_result["success"]:
                if user_id in telegram_sessions:
                    del telegram_sessions[user_id]
                return verify_result
            
            api_result = telegram_api.get_api_credentials()
            
            if user_id in telegram_sessions:
                del telegram_sessions[user_id]
            
            if api_result["success"]:
                update_data(f"""
                    UPDATE user SET 
                    api_id = '{api_result['api_id']}',
                    api_hash = '{api_result['api_hash']}',
                    step = 'api_received-{api_result['api_id']}-{api_result['api_hash']}-{code}'
                    WHERE id = '{user_id}'
                """)
            
            return api_result
            
    except Exception as e:
        if user_id in telegram_sessions:
            del telegram_sessions[user_id]
        return {"success": False, "message": f"خطای سیستمی: {str(e)[:100]}"}

async def start_auto_api_process(user_id, phone_number):
    try:
        telegram_api = TelegramAPIAuto()
        result = telegram_api.send_phone(phone_number)
        
        if not result["success"]:
            return result
        
        telegram_sessions[user_id] = {
            "api": telegram_api,
            "phone": phone_number,
            "random_hash": result["random_hash"],
            "timestamp": time.time()
        }
        
        return {
            "success": True,
            "message": "کد تأیید ارسال شد",
            "requires_code": True
        }
        
    except Exception as e:
        return {"success": False, "message": f"خطا: {str(e)[:100]}"}

async def verify_and_get_api(user_id, code):
    try:
        if user_id not in telegram_sessions:
            return {"success": False, "message": "جلسه منقضی شده"}
        
        session_data = telegram_sessions[user_id]
        telegram_api = session_data["api"]
        verify_result = telegram_api.verify_code(
            session_data["phone"],
            session_data["random_hash"],
            code
        )
        
        if not verify_result["success"]:
            return verify_result
        
        api_result = telegram_api.get_api_credentials()
        
        if user_id in telegram_sessions:
            del telegram_sessions[user_id]
        
        return api_result
        
    except Exception as e:
        if user_id in telegram_sessions:
            del telegram_sessions[user_id]
        return {"success": False, "message": f"خطا: {str(e)[:100]}"}


async def show_api_info(chat_id, api_result, message_id=None):
    try:
        api_id = api_result["api_id"]
        api_hash = api_result["api_hash"]
        
        update_data(f"""
            UPDATE user SET 
            api_id = '{api_id}',
            api_hash = '{api_hash}',
            step = 'api_ready'
            WHERE id = '{chat_id}'
        """)
        
        masked_hash = f"{api_hash[:4]}{'*' * (len(api_hash)-8)}{api_hash[-4:]}"
        
        message = f"""**
**📞 Number : `{user_info['phone']}`
🆔 Api ID : `{api_id}`
🆔 Api Hash : `{masked_hash}`
                    
• آیا اطلاعات را تایید میکنید؟          ‌‌‌‌ 
**"""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("بله (✅)", callback_data="ConfirmInstall"),
            InlineKeyboardButton("خیر (❎)", callback_data="ChangeInfo")],
            [InlineKeyboardButton("(🔙) بازگشت", callback_data="Back")]
        ])
        
        if message_id:
            try:
                await app.edit_message_text(
                    chat_id,
                    message_id,
                    message,
                    reply_markup=keyboard
                )
            except:
                await app.send_message(
                    chat_id,
                    message,
                    reply_markup=keyboard
                )
        else:
            await app.send_message(
                chat_id,
                message,
                reply_markup=keyboard
            )
        
        return True
        
    except Exception as e:
        try:
            await app.send_message(
                chat_id,
                "**✅ API اطلاعات دریافت شد**\n"
                "لطفا از منوی اصلی ادامه دهید.",
            )
        except:
            pass
        return False

telegram_sessions = {}

def generate_payment_invoice(user_id, amount, description=None, email=None, mobile=None):
    try:
        gateway_status = get_gateway_status()
        
        if not gateway_status["active"]:
            return {"success": False, "message": "درگاه پرداخت غیرفعال است"}
        
        merchant_id = gateway_status.get("merchant_id", "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        is_sandbox = gateway_status.get("sandbox", True)
        
        if is_sandbox:
            base_url = "https://sandbox.zarinpal.com/pg/v4/payment/"
        else:
            base_url = "https://api.zarinpal.com/pg/v4/payment/"
        
        url = base_url + "request.json"
        
        data = {
            "merchant_id": merchant_id,
            "amount": int(amount) * 10,
            "callback_url": "https://self.oghabvip.ir/index.html",
            "description": description or f"{user_id} - خرید ربات دستیار تلگرام",
            "metadata": {
                "user_id": str(user_id),
                "mobile": mobile[:11] if mobile else None
            }
        }
        
        data["metadata"] = {k: v for k, v in data["metadata"].items() if v}
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ZarinPal-API/1.0"
        }
        
        urllib3.disable_warnings() # For Cpanwl
        
        response = requests.post(
            url,
            json=data,
            headers=headers,
            timeout=30,
            verify=False, # For Cpanel
            proxies=None
        )
        
        if response.status_code == 200:
            result = response.json()
            if "data" in result and result["data"].get("code") == 100:
                authority = result["data"]["authority"]
                
                if is_sandbox:
                    payment_url = f"https://sandbox.zarinpal.com/pg/StartPay/{authority}"
                else:
                    payment_url = f"https://zarinpal.com/pg/StartPay/{authority}"
                
                return {
                    "success": True,
                    "authority": authority,
                    "payment_url": payment_url,
                    "message": "لینک پرداخت ایجاد شد"
                }
            else:
                error_code = result.get("data", {}).get("code", "unknown")
                return {"success": False, "message": f"خطا از زرین‌پال: کد {error_code}"}
        else:
            return {"success": False, "message": f"خطای HTTP: {response.status_code}"}
            
    except requests.exceptions.Timeout:
        return {"success": False, "message": "اتصال timeout شد"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "خطا در اتصال به اینترنت"}
    except Exception as e:
        return {"success": False, "message": f"خطای سیستمی: {str(e)[:100]}"}

def verify_payment(authority, amount):
    gateway_status = get_gateway_status()
    
    if gateway_status["sandbox"]:
        base_url = "https://sandbox.zarinpal.com/pg/v4/payment/"
    else:
        base_url = "https://api.zarinpal.com/pg/v4/payment/"
    
    url = base_url + "verify.json"
    
    merchant_id = gateway_status.get("merchant_id", "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
    
    # اصلاح: مقدار amount باید از دیتابیس خوانده شود
    amount_in_rial = amount * 10
    
    data = {
        "merchant_id": merchant_id,
        "authority": authority,
        "amount": amount_in_rial,
    }
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        response = requests.post(
            url, 
            json=data, 
            headers=headers, 
            timeout=30,
            verify=False # For Cpanel
        )
        
        if response.status_code != 200:
            return {
                "success": False,
                "message": f"خطا در اتصال به زرین‌پال. کد وضعیت: {response.status_code}"
            }
        
        result = response.json()
        
        if "data" in result and result["data"] is not None:
            code = result["data"].get("code")
            
            # اصلاح: بررسی صحیح کدهای موفقیت
            if code in [100, 101]:
                ref_id = result["data"].get("ref_id")
                
                return {
                    "success": True,
                    "ref_id": ref_id,
                    "code": code,
                    "message": "پرداخت با موفقیت تأیید شد" if code == 100 else "پرداخت قبلاً تأیید شده است"
                }
            else:
                error_code = code
        else:
            error_code = result.get("errors", {}).get("code", "unknown")
        
        error_codes = {
            100: "پرداخت موفق",
            101: "پرداخت قبلاً تأیید شده",
            -1: "اطلاعات ارسال شده ناقص است",
            -2: "IP یا مرچنت کد پذیرنده صحیح نیست",
            -3: "با توجه به محدودیت‌های شاپرک امکان پرداخت با رقم درخواست شده میسر نیست",
            -4: "سطح تایید پذیرنده پایین‌تر از سطح نقره‌ای است",
            -11: "درخواست مورد نظر یافت نشد",
            -21: "هیچ نوع عملیات مالی برای این تراکنش یافت نشد",
            -22: "تراکنش ناموفق می‌باشد",
            -33: "رقم تراکنش با رقم پرداخت شده مطابقت ندارد",
            -34: "سقف تقسیم تراکنش از لحاظ رقم یا تعداد عبور نموده است",
            -40: "اجازه دسترسی به متد مربوطه وجود ندارد",
            -54: "درخواست مورد نظر آرشیو شده است",
            -100: "خطای داخلی سرور",
            -101: "تراکنش با این کد پیگیری موجود نیست",
            -102: "زمان مجاز برای تأیید پرداخت به پایان رسیده است"
        }
        
        error_msg = error_codes.get(error_code, f"خطای ناشناخته: {error_code}")
        
        if result.get("errors"):
            error_details = result["errors"].get("validations", {}).get("message", "بدون جزئیات")
            error_msg += f" - {error_details}"
        
        return {
            "success": False,
            "message": f"پرداخت ناموفق. {error_msg}"
        }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": "اتصال به زرین‌پال timeout شد. لطفا دوباره تلاش کنید."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"خطا در تأیید پرداخت: {str(e)[:200]}"
        }

def save_payment_transaction(user_id, authority, amount, plan_days, status="pending"):
    query = f"""
    INSERT INTO payment_transactions 
    (user_id, authority, amount, plan_days, status, created_at) 
    VALUES ({user_id}, '{authority}', {amount}, {plan_days}, '{status}', NOW())
    """
    update_data(query)
    transaction = get_data(f"SELECT * FROM payment_transactions WHERE authority = '{authority}' ORDER BY id DESC LIMIT 1")
    return transaction

def update_payment_transaction(authority, status, ref_id=None):
    if ref_id:
        query = f"UPDATE payment_transactions SET status = '{status}', ref_id = '{ref_id}', updated_at = NOW() WHERE authority = '{authority}'"
    else:
        query = f"UPDATE payment_transactions SET status = '{status}', updated_at = NOW() WHERE authority = '{authority}'"
    
    update_data(query)
    return get_data(f"SELECT * FROM payment_transactions WHERE authority = '{authority}' LIMIT 1")

@lru_cache(maxsize=100)
def get_setting(key, default=None):
    default_settings = {
        "start_message": "**سلام {user_link}، به ربات خرید دستیار تلگرام خوش آمدید!**",
        "price_message": "**نرخ ربات دستیار عبارت است از :\n\n» 1 ماهه : ( `{price_1month}` تومان )\n\n» 2 ماهه : ( `{price_2month}` تومان )\n\n» 3 ماهه : ( `{price_3month}` تومان )\n\n» 4 ماهه : ( `{price_4month}` تومان )\n\n» 5 ماهه : ( `{price_5month}` تومان )\n\n» 6 ماهه : ( `{price_6month}` تومان )**",
        "whatself_message": "**سلف به رباتی گفته میشه که روی اکانت شما نصب میشه و امکانات خاصی رو در اختیارتون میزاره.**",
        "price_1month": "75000",
        "price_2month": "150000",
        "price_3month": "220000",
        "price_4month": "275000",
        "price_5month": "340000",
        "price_6month": "390000",
        "card_number": CardNumber,
        "card_name": CardName,
        "phone_restriction": "enabled"
    }
    
    try:
        result = get_data(f"SELECT setting_value FROM settings WHERE setting_key = '{key}'")
        
        if result and isinstance(result, dict):
            value = result.get('setting_value')
            if value is not None and str(value).strip() != '':
                return str(value)
    
    except Exception as e:
        pass
    return default_settings.get(key, default)

def update_setting(key, value):
    update_data("UPDATE settings SET setting_value = %s WHERE setting_key = %s", params=[value, key])
    
    with _cache_lock:
        cache_key = f"setting_{key}"
        if cache_key in _settings_cache:
            del _settings_cache[cache_key]
        get_setting.cache_clear()

def get_all_settings():
    return get_datas("SELECT * FROM settings ORDER BY id")

def get_prices():
    return {
        "1month": get_setting("price_1month", "75000"),
        "2month": get_setting("price_2month", "150000"),
        "3month": get_setting("price_3month", "220000"),
        "4month": get_setting("price_4month", "275000"),
        "5month": get_setting("price_5month", "340000"),
        "6month": get_setting("price_6month", "390000"),
    }

_keyboard_cache = {}

@lru_cache(maxsize=1000)
def get_main_keyboard(user_id, expir, is_admin=False, has_self_folder=False, current_lang="fa"):
    cache_key = f"keyboard_{user_id}_{expir}_{is_admin}_{has_self_folder}_{current_lang}"
    
    if cache_key in _keyboard_cache:
        keyboard_data, timestamp = _keyboard_cache[cache_key]
        if time.time() - timestamp < 30:
            return InlineKeyboardMarkup(keyboard_data)
    
    keyboard = []
    keyboard.append([InlineKeyboardButton(text="پشتیبانی 👨‍💻", callback_data="Support")])
    
    keyboard.append([
        InlineKeyboardButton(text="راهنما 🗒️", url=f"https://t.me/{Channel_Help}"),
        InlineKeyboardButton(text="دستیار چیست؟ 🧐", callback_data="WhatSelf")
    ])
    
    expiry_display = format_expiry_time(expir)
    keyboard.append([InlineKeyboardButton(text=f"انقضا: ( {expiry_display} )", callback_data="ExpiryStatus")])
    
    keyboard.append([
        InlineKeyboardButton(text="خرید اشتراک 💵", callback_data="BuySub"),
        InlineKeyboardButton(text="احراز هویت ✔️", callback_data="AccVerify")
    ])
    
    if expir > 0:
        keyboard.append([InlineKeyboardButton(text="تمدید با کد 💶", callback_data="BuyCode")])
    else:
        keyboard.append([InlineKeyboardButton(text="خرید با کد 💶", callback_data="BuyCode")])
        
    if is_admin:
        keyboard.append([InlineKeyboardButton(text="مدیریت 🎈", callback_data="AdminPanel")])
    
    keyboard.append([InlineKeyboardButton(text="نرخ 💎", callback_data="Price")])
    
    if expir > 0:
        if has_self_folder:
            lang_display = "فارسی 🇮🇷" if current_lang == "fa" else "انگلیسی 🇬🇧"
            
            keyboard.extend([
                [
                    InlineKeyboardButton(text="ورود/نصب ⏏️", callback_data="InstallSelf"),
                    InlineKeyboardButton(text="تغییر زبان 🇬🇧", callback_data="ChangeLang")
                ],
                [InlineKeyboardButton(text="وضعیت ⚙️", callback_data="SelfStatus")],
                [InlineKeyboardButton(text=f"زبان: {lang_display}", callback_data="text")]
            ])
        else:
            keyboard.extend([
                [
                    InlineKeyboardButton(text="ورود/نصب ⏏️", callback_data="InstallSelf"),
                    InlineKeyboardButton(text="تغییر زبان 🇬🇧", callback_data="ChangeLang")
                ],
                [InlineKeyboardButton(text="وضعیت ⚙️", callback_data="SelfStatus")]
            ])
    
    keyboard.append([InlineKeyboardButton(text="کانال ما 📢", url=f"https://t.me/{Channel_ID}")])
    
    _keyboard_cache[cache_key] = (keyboard, time.time())
    
    return InlineKeyboardMarkup(keyboard)

AdminPanelKeyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(text="آمار 📊", callback_data="AdminStats")],
        [InlineKeyboardButton(text="ارسال همگانی", callback_data="AdminBroadcast"),
         InlineKeyboardButton(text="فوروارد همگانی ✉️", callback_data="AdminForward")],
        [InlineKeyboardButton(text="بلاک کاربر 🚫", callback_data="AdminBlock"),
         InlineKeyboardButton(text="آنبلاک کاربر ✅️", callback_data="AdminUnblock")],
        [InlineKeyboardButton(text="افزودن انقضا ➕", callback_data="AdminAddExpiry"),
         InlineKeyboardButton(text="کسر انقضا ➖", callback_data="AdminDeductExpiry")],
        [InlineKeyboardButton(text="فعال کردن سلف 🔵", callback_data="AdminActivateSelf"),
         InlineKeyboardButton(text="غیرفعال کردن سلف 🔴", callback_data="AdminDeactivateSelf")],
        [InlineKeyboardButton(text="ساخت کد 🔑", callback_data="AdminCreateCode"),
         InlineKeyboardButton(text="لیست کدها 📋", callback_data="AdminListCodes")],
        [InlineKeyboardButton(text="حذف کد ❌", callback_data="AdminDeleteCode")],
        [InlineKeyboardButton(text="روشن کردن ربات 🔵", callback_data="AdminTurnOn"),
         InlineKeyboardButton(text="خاموش کردن ربات 🔴", callback_data="AdminTurnOff")],
        [InlineKeyboardButton(text="تنظیمات ⚙️", callback_data="AdminSettings")],
        [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="Back")]
    ]
)

AdminSettingsKeyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(text="تغییر متن استارت 📝", callback_data="EditStartMessage")],
        [InlineKeyboardButton(text="تغییر متن نرخ 💰", callback_data="EditPriceMessage")],
        [InlineKeyboardButton(text="تغییر متن سلف 🤖", callback_data="EditSelfMessage")],
        [InlineKeyboardButton(text="تغییر قیمت‌ها 📊", callback_data="EditPrices")],
        [InlineKeyboardButton(text="تغییر اطلاعات کارت 💳", callback_data="EditCardInfo")],
        [InlineKeyboardButton(text="محدودیت شماره 📱", callback_data="PhoneRestriction")],
        [InlineKeyboardButton(text="تنظیمات درگاه پرداخت 🏦", callback_data="GatewaySettings")],  # اضافه شد
        [InlineKeyboardButton(text="مشاهده تنظیمات 👁️", callback_data="ViewSettings")],
        [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]
    ]
)

@app.on_message(filters.private, group=-1)
async def update(c, m):
    user_id = m.chat.id
    user_cache_key = f"user_full_{user_id}"
    with _cache_lock:
        if user_cache_key not in _user_cache:
            if get_data("SELECT id FROM user WHERE id = %s", params=[user_id]) is None:
                update_data("INSERT INTO user(id) VALUES(%s)", params=[user_id])
                invalidate_user_cache(user_id)


@app.on_inline_query()
async def inline_code_handler(client, inline_query):
    query = inline_query.query.strip()
    user_id = inline_query.from_user.id
    
    user = get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1")
    
    if user and user["step"].startswith("install_code-"):
        if not query:
            return
        
        if not query.isdigit():
            return
        
        if len(query) < 5:
            return
        
        code = query[:5]
        
        if len(code) == 5:
            step_parts = user["step"].split("-")
            if len(step_parts) >= 4:
                phone = step_parts[1]
                api_id = step_parts[2]
                api_hash = step_parts[3]
                
                results = [
                    InlineQueryResultArticle(
                        title="دریافت کد",
                        description=f"کد وارد شده شما : ( {code} )",
                        id="1",
                        input_message_content=InputTextMessageContent(
                            message_text=f"**تنظیم شد.**")
                        )]
                
                await inline_query.answer(
                    results=results,
                    cache_time=0,
                    is_personal=True
                )
                
                await asyncio.sleep(0.5)
                
                try:
                    success = await verify_code_and_login(user_id, phone, api_id, api_hash, code)
                    
                    if success:
                        await app.send_message(
                            user_id,
                            "**• ورود به اکانت با موفقیت انجام شد، درحال نصب نهایی سلف، لطفا صبور باشید.**"
                        )
                    else:
                        pass
                        
                except Exception as e:
                    await app.send_message(
                        user_id,
                        "**خطا، با پشتیبانی در ارتباط باشید.**"
                    )

@app.on_message(filters.private & filters.command("start"))
@checker 
async def force_start(c, m):
    try:
        chat_id = m.chat.id
        
        ensure_user_exists(chat_id)
        
        user_data = get_data("SELECT expir FROM user WHERE id = %s", params=[chat_id])
        expir = user_data.get("expir", 0) if user_data else 0
        
        is_admin = (chat_id == Admin) or (helper_getdata(f"SELECT * FROM adminlist WHERE id = '{chat_id}' LIMIT 1") is not None)
        
        has_self_folder = os.path.isdir(f"selfs/self-{chat_id}")
        current_lang = get_current_language(chat_id)
        keyboard = get_main_keyboard(
            user_id=chat_id,
            expir=expir,
            is_admin=is_admin,
            has_self_folder=has_self_folder,
            current_lang=current_lang
        )
        
        user_link = f'<a href="tg://user?id={chat_id}">{html.escape(m.chat.first_name)}</a>'
        start_message = get_setting("start_message").format(user_link=user_link)
        
        await app.send_message(chat_id, start_message, reply_markup=keyboard)
        
        update_data("UPDATE user SET step = 'none' WHERE id = %s", params=[chat_id])
        
        async with lock:
            if chat_id in temp_Client:
                del temp_Client[chat_id]
        
    except Exception as e:
        try:
            await app.send_message(m.chat.id, "**سلام! به ربات خوش آمدید. لطفا دوباره امتحان کنید.**")
        except:
            pass

_callback_cache = {}

@app.on_callback_query()
@checker
async def callback_handler(c, call):
    global temp_Client
    user = get_data(f"SELECT * FROM user WHERE id = '{call.from_user.id}' LIMIT 1")
    phone_number = user["phone"] if user else None
    expir = user["expir"] if user else 0
    chat_id = call.from_user.id
    m_id = call.message.id
    data = call.data
    username = f"@{call.from_user.username}" if call.from_user.username else "وجود ندارد"
		
    if data == "BuySub" or data == "Back2":
        user_info = get_user_info(call.from_user.id)
        if not user_info:
            await app.answer_callback_query(call.id, text="خطا در دریافت اطلاعات کاربر", show_alert=True)
            return
        
        if user["phone"] is None:
            await app.delete_messages(chat_id, m_id)
            await app.send_message(chat_id, "**لطفا با استفاده از دکمه زیر شماره موبایل خود را به اشتراک بگذارید.**", reply_markup=ReplyKeyboardMarkup(
                [
                    [
                        KeyboardButton(text="اشتراک گذاری شماره", request_contact=True)
                    ]
                ],resize_keyboard=True
            ))
            update_data(f"UPDATE user SET step = 'contact' WHERE id = '{call.from_user.id}' LIMIT 1")
        else:
            user_cards = get_user_cards(call.from_user.id)
            if user_cards:
                keyboard_buttons = []
                for card in user_cards:
                    card_number = card["card_number"]
                    bank_name = card["bank_name"] if card["bank_name"] else "نامشخص"
                    masked_card = f"{card_number[:4]} - - - - - - {card_number[-4:]}"
                    keyboard_buttons.append([
                        InlineKeyboardButton(text=masked_card, callback_data=f"SelectCardForPayment-{card['id']}")
                    ])
                keyboard_buttons.append([InlineKeyboardButton(text="(🔙) بازگشت", callback_data="Back")])
                
                await app.edit_message_text(chat_id, m_id,
                    "**• لطفا انتخاب کنید برای پرداخت از کدام کارت احراز شده ی خود میخواهید استفاده کنید.**",
                    reply_markup=InlineKeyboardMarkup(keyboard_buttons))
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")
            else:
                await app.edit_message_text(chat_id, m_id,
                    "**• برای خرید باید ابتدا احراز هویت کنید.**",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(text="احراز هویت ✔️", callback_data="AccVerify")]
                    ]))
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data.startswith("SelectCardForPayment-"):
        card_id = data.split("-")[1]
        card = get_card_by_id(card_id)
        if card:
            gateway_status = get_gateway_status()
        
            if gateway_status["active"]:
                update_data(f"UPDATE user SET step = 'select_subscription_gateway-{card_id}' WHERE id = '{call.from_user.id}' LIMIT 1")
            else:
                update_data(f"UPDATE user SET step = 'select_subscription_manual-{card_id}' WHERE id = '{call.from_user.id}' LIMIT 1")
        
            prices = get_prices()
        
            if gateway_status["active"]:
            
                await app.edit_message_text(chat_id, m_id,
                    "**• لطفا از کزینه های زیر انتخاب کنید میخواهید ربات دستیار را برای چند ماه خریداری کنید.**",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(text=f"( 1 ) ماه معادل {prices['1month']} تومان", callback_data=f"PayGateway-31-{prices['1month']}-{card_id}")],
                        [InlineKeyboardButton(text=f"( 2 ) ماه معادل {prices['2month']} تومان", callback_data=f"PayGateway-62-{prices['2month']}-{card_id}")],
                        [InlineKeyboardButton(text=f"( 3 ) ناه معادل {prices['3month']} تومان", callback_data=f"PayGateway-93-{prices['3month']}-{card_id}")],
                        [InlineKeyboardButton(text=f"( 4 ) ماه معادل {prices['4month']} تومان", callback_data=f"PayGateway-124-{prices['4month']}-{card_id}")],
                        [InlineKeyboardButton(text=f"( 5 ) ماه معادل {prices['5month']} تومان", callback_data=f"PayGateway-155-{prices['5month']}-{card_id}")],
                        [InlineKeyboardButton(text=f"( 6 ) ماه معادل {prices['6month']} تومان", callback_data=f"PayGateway-186-{prices['6month']}-{card_id}")],
                        [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="BuySub")]
                    ]))
            else:
                await app.edit_message_text(chat_id, m_id,
                    "**• لطفا از گزینه های زیر انتخاب کنید میخواهید ربات دستیار را برای چند ماه خریداری کنید.**",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(text=f"( 1 ) ماه معادل {prices['1month']} تومان", callback_data=f"Sub-31-{prices['1month']}")],
                        [InlineKeyboardButton(text=f"( 2 ) ماخ معادل {prices['2month']} تومان", callback_data=f"Sub-62-{prices['2month']}")],
                        [InlineKeyboardButton(text=f"( 3 ) ماه معادل {prices['3month']} تومان", callback_data=f"Sub-93-{prices['3month']}")],
                        [InlineKeyboardButton(text=f"( 4 ) ماه معادل {prices['4month']} تومان", callback_data=f"Sub-124-{prices['4month']}")],
                        [InlineKeyboardButton(text=f"( 5 ) ماه معادل {prices['5month']} تومان", callback_data=f"Sub-155-{prices['5month']}")],
                        [InlineKeyboardButton(text=f"( 6 ) ماه معادل {prices['6month']} تومان", callback_data=f"Sub-186-{prices['6month']}")],
                        [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="BuySub")]
                    ]))
    
    elif data.startswith("PayGateway-"):
    # پرداخت از طریق درگاه
        params = data.split("-")
        expir_count = int(params[1])
        cost = int(params[2])
        card_id = params[3]
        card = get_card_by_id(card_id)
        if not card:
            await app.answer_callback_query(call.id, text="کارت مورد نظر یافت نشد", show_alert=True)
            return
    
        card_number = card["card_number"]
        bank_name = card["bank_name"] or "نامشخص"
        description = f"خرید اشتراک {expir_count} روزه دستیار تلگرام"
    
        user_data = get_data(f"SELECT phone FROM user WHERE id = '{chat_id}' LIMIT 1")
        user_phone = user_data["phone"] if user_data else None
    
        payment_result = generate_payment_invoice(
            user_id=chat_id,
            amount=cost,
            description=description,
            mobile=user_phone
        )
    
        if payment_result["success"]:
            transaction = save_payment_transaction(
                user_id=chat_id,
                authority=payment_result["authority"],
                amount=cost,
                plan_days=expir_count,
                status="pending"
            )
        
            if expir_count == 31:
                month_text = "1 ماه"
            elif expir_count == 62:
                month_text = "2 ماه"
            elif expir_count == 93:
                month_text = "3 ماه"
            elif expir_count == 124:
                month_text = "4 ماه"
            elif expir_count == 155:
                month_text = "5 ماه"
            elif expir_count == 186:
                month_text = "6 ماه"
            else:
                month_text = f"{expir_count} روز"
        
            invoice_message = f"""**
فاکتور خرید دستیار برای {month_text} ایجاد شد.
توجه :
• با کارتی که احراز کردید خرید کنید.
 ‌ شماره کارت شما : `{card_number} - {bank_name}`
• بعد از پرداخت بر روی دکمه اعتبار سنجی بزنید.
            **"""
    
        
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 پرداخت درگاه امن", url=payment_result["payment_url"])],
                [InlineKeyboardButton("⌛️ اعتبار سنجی", callback_data=f"VerifyPayment-{payment_result['authority']}")]
            ])
        
            await app.edit_message_text(chat_id, m_id, invoice_message, reply_markup=keyboard)
            
            await app.send_message(
                chat_id,
                "**• در صورتی که درگاه براتون بالا نمیاد، با فیلترشکن (VPN) و بدونش رو تست بفرمایید.**",
                reply_to_message_id=m_id
            )
            
        else:
            await app.answer_callback_query(call.id, text=f"خطا در ایجاد لینک پرداخت: {payment_result['message']}", show_alert=True)

    elif data.startswith("VerifyPayment-"):
        authority = data.split("-")[1]
       
        transaction = get_data(f"SELECT * FROM payment_transactions WHERE authority = '{authority}' AND user_id = '{chat_id}' LIMIT 1")
        
        if not transaction:
            await app.answer_callback_query(call.id, text="• تراکنش یافت نشد •", show_alert=True)
            return
        
        if transaction["status"] == "pending":
            verify_result = verify_payment(authority, transaction["amount"])
            
            if not verify_result["success"]:
                await app.answer_callback_query(
                    call.id, 
                    text=f"• این فاکتور پرداخت نشده؛\nو یا با کارتی غیر از کارت احراز شده پرداخت شده.\n( هزینه از سمت درگاه بازگشت میابد. )",
                    show_alert=True
                )
                return
        
        await app.answer_callback_query(call.id, text="• درحال بررسی •", show_alert=False)
        
        verify_result = verify_payment(authority, transaction["amount"])
        
        if verify_result["success"]:
            # پرداخت موفق
            update_payment_transaction(authority, "success", verify_result["ref_id"])
            
            user_data = get_data(f"SELECT expir FROM user WHERE id = '{chat_id}' LIMIT 1")
            old_expir = user_data["expir"] if user_data else 0
            new_expir = old_expir + transaction["plan_days"]
            
            update_data(f"UPDATE user SET expir = '{new_expir}' WHERE id = '{chat_id}' LIMIT 1")
            
            plan_days = transaction["plan_days"]
            
            if plan_days == 31:
                month_text = "یک ماه"
            elif plan_days == 62:
                month_text = "دو ماه"
            elif plan_days == 93:
                month_text = "سه ماه"
            elif plan_days == 124:
                month_text = "چهار ماه"
            elif plan_days == 155:
                month_text = "پنج ماه"
            elif plan_days == 186:
                month_text = "شش ماه"
            else:
                month_text = f"{plan_days} روز"
            
            success_message = f"""**• پرداخت با موفقیت انجام شد.
• شناسه مرجع : ( `{verify_result['ref_id']}` )
• انقضای سلف شما {month_text} اضافه گردید.
                
• انقضای قبلی شما : ( `{old_expir}` روز )
                
• انقضای جدید : ( `{new_expir}` روز )
                **"""
            
            await app.edit_message_text(
                chat_id, 
                call.message.id,
                success_message
            )
            
            user_info = await app.get_users(chat_id)
            username = f"@{user_info.username}" if user_info.username else "ندارد"
            
            await app.send_message(
                Admin,
                f"**• خرید آنلاین #اشتراک :\n"
                f"• نام: ( {html.escape(user_info.first_name)} )\n"
                f"• یوزرنیم: ( {username} )\n"
                f"• آیدی عددی: ( `{chat_id}` )\n"
                f"• مبلغ: ( `{transaction['amount']:,}` تومان )\n"
                f"• روزهای اضافه شده: ( `{transaction['plan_days']}` )\n"
                f"• انقضای جدید: ( `{new_expir}` روز )\n"
                f"• شناسه مرجع: ( `{verify_result['ref_id']}` )**"
            )
            
        else:
            update_payment_transaction(authority, "failed")
            
            error_message = f"**• پرداخت تأیید نشد: {verify_result['message']}**"
            
            await app.edit_message_text(
                chat_id, 
                call.message.id,
                error_message
            )
    
    elif data.startswith("Sub-"):
        params = data.split("-")
        expir_count = params[1]
        cost = params[2]
        card_id = user["step"].split("-")[1]
        card = get_card_by_id(card_id)
    
        if card:
            card_number = card["card_number"]
            masked_card = f"{card_number[:4]} - - - - - - {card_number[-4:]}"
        
            bot_card_number = get_setting("card_number")
            bot_card_name = get_setting("card_name")
        
            await app.edit_message_text(chat_id, m_id, f"**• لطفا مبلغ ( `{cost}` تومان ) رو با کارتی که احراز هویت و انتخاب کردید یعنی [ `{card_number}` ] به کارت زیر واریز کنید و فیش واریز خود را همینجا ارسال کنید.\n\n[ `{bot_card_number}` ]\nبه نام : {bot_card_name}\n\n• ربات آماده دریافت فیش واریزی شماست :**")
        
            update_data(f"UPDATE user SET step = 'payment_receipt-{expir_count}-{cost}-{card_id}' WHERE id = '{call.from_user.id}' LIMIT 1")

    
    elif data == "Price":
        prices = get_prices()
        price_message = get_setting("price_message").format(
            price_1month=prices["1month"],
            price_2month=prices["2month"],
            price_3month=prices["3month"],
            price_4month=prices["4month"],
            price_5month=prices["5month"],
            price_6month=prices["6month"]
        )
        await app.edit_message_text(chat_id, m_id, price_message, 
                       reply_markup=InlineKeyboardMarkup([
                                   [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="Back")]
                               ]))
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data == "AccVerify":
        user_cards = get_user_cards(call.from_user.id, only_verified=True)
    
        if user_cards:
            cards_text = f"**• به منوی احراز هویت خوش آمدید:\n\nکارت های احراز شده :\n⁭⁯⁯⁭⁯**"
            for idx, card in enumerate(user_cards, 1):
                card_number = card["card_number"]
                bank_name = card["bank_name"] if card["bank_name"] else "نامشخص"
                masked_card = f"{card_number[:4]} - - - - - - {card_number[-4:]}"
                cards_text += f"**{idx} - {bank_name} [ `{card_number}` ] \n‌‌‌‌‌ ‌‌‌‌‌‌‌‌ ‌ ‌ ‌‌‌‌‌‌‌‌ ‌‌‌‌‌‌‌‌‌ ‌‌‌‌‌‌‌\n ‌‌‌‌‌ ‌‌‌‌‌‌‌‌‌‌ ‌‌‌  ‌‌‌‌‌‌‌‌‌ ‌‌‌‌‌‌**"
        
            keyboard_buttons = []
            keyboard_buttons.append(
                [InlineKeyboardButton(text="کارت جدید ➕", callback_data="AddNewCard"),
                InlineKeyboardButton(text="حذف کارت ➖", callback_data="DeleteCard")])
            keyboard_buttons.append(
                [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="Back")])
        
            await app.edit_message_text(chat_id, m_id, cards_text, 
                                   reply_markup=InlineKeyboardMarkup(keyboard_buttons))
        else:
            await app.edit_message_text(chat_id, m_id, 
                                   "**• به منوی احراز هویت خوش آمدید ، لطفا انتخاب کنید:**",
                                   reply_markup=InlineKeyboardMarkup([
                                       [InlineKeyboardButton(text="➕ کارت جدید", callback_data="AddNewCard"),
                                       InlineKeyboardButton(text="حذف کارت ➖", callback_data="DeleteCard")],
                                       [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="Back")]
                                   ]))
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data == "AddNewCard":
        await app.edit_message_text(chat_id, m_id, """**• به بخش احراز هویت خوش آمدید.  برای احراز هویت از کارت خود ( حتما کارتی که با آن میخواهید پرداخت انجام دهید ) عکس بگیرید و ارسال کنید.  
• اسم و فامیل شما روی کارت باید کاملا مشخص باشد و عکس کارت داخل برنامه قابل قبول نمیباشد...

• نکات :
1) شماره کارت و نام صاحب کارت کاملا مشخص باشد.
2) لطفا تاریخ اعتبار و Cvv2 کارت خود را بپوشانید!
3) فقط با کارتی که احراز هویت میکنید میتوانید خرید انجام بدید و اگر با کارت دیگری اقدام کنید تراکنش ناموفق میشود و هزینه از سمت خودِ بانک به شما بازگشت داده میشود.
4) در صورتی که توانایی ارسال عکس از کارت را ندارید تنها راه حل ارسال عکس از کارت ملی یا شناسنامه صاحب کارت است.

لطفا عکس از کارتی که میخواهید با آن خرید انجام دهید ارسال کنید...**""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AccVerify")]
        ]))
        update_data(f"UPDATE user SET step = 'card_photo' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data == "DeleteCard":
        user_cards = get_user_all_cards(call.from_user.id, only_verified=True)
    
        verified_cards = [card for card in user_cards if card["verified"] == "verified"]
    
        if verified_cards:
            keyboard_buttons = []
            for card in verified_cards:
                card_number = card["card_number"]
                masked_card = f"{card_number[:4]} - - - - - - {card_number[-4:]}"
                keyboard_buttons.append([
                    InlineKeyboardButton(text=masked_card, callback_data=f"SelectCard-{card['id']}")
                ])
            keyboard_buttons.append([InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AccVerify")])
        
            await app.edit_message_text(chat_id, m_id,
                                   "**• لطفا انتخاب کنید میخواهید کدام کارت خود را حذف کنید.**",
                                   reply_markup=InlineKeyboardMarkup(keyboard_buttons))
        else:
            await app.answer_callback_query(call.id, text="• هیچ کارت احراز هویت شده ای برای حذف ندارید •", show_alert=True)

    elif data.startswith("SelectCard-"):
        card_id = data.split("-")[1]
        card = get_card_by_id(card_id)
        if card:
            card_number = card["card_number"]
            masked_card = f"{card_number[:4]} - - - - - - {card_number[-4:]}"
            await app.edit_message_text(chat_id, m_id,
                                       f"**• آیا مطمئن هستید که میخواهید کارت [ `{masked_card}` ] را حذف کنید؟**",
                                       reply_markup=InlineKeyboardMarkup([
                                           [InlineKeyboardButton(text="بله", callback_data=f"ConfirmDelete-{card_id}"),
                                            InlineKeyboardButton(text="خیر", callback_data="AccVerify")]
                                       ]))

    elif data.startswith("ConfirmDelete-"):
        card_id = data.split("-")[1]
        card = get_card_by_id(card_id)
        if card:
            card_number = card["card_number"]
            bank_name = card["bank_name"] if card["bank_name"] else "نامشخص"
            masked_card = f"{card_number[:4]} - - - - - - {card_number[-4:]}"
            delete_card(card_id)
            await app.edit_message_text(chat_id, m_id,
                                       f"**• کارت ( `{bank_name}` - `{card_number}` ) با موفقیت حذف شد.**",
                                       reply_markup=InlineKeyboardMarkup([
                                           [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AccVerify")]
                                       ]))

    elif data == "WhatSelf":
        whatself_message = get_setting("whatself_message")
        await app.edit_message_text(chat_id, m_id, whatself_message, 
                               reply_markup=InlineKeyboardMarkup([
                                   [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="Back")]
                               ]))
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data == "Support":
        await app.edit_message_text(chat_id, m_id, "**• شما با موفقیت به پشتیبانی متصل شدید!\nلطفا دقت کنید که توی پشتیبانی اسپم ندید و از دستورات سلف توی پشتیبانی استفاده نکنید، اکنون میتوانید پیام خود را ارسال کنید.**", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="دستیارم کار نمیکنه 🪫", callback_data="SelfStatus")],
                    [InlineKeyboardButton(text="لغو اتصال 💥", callback_data="Back")
                ]
			]
        ))
        update_data(f"UPDATE user SET step = 'support' WHERE id = '{call.from_user.id}' LIMIT 1")
    
    elif data.startswith("ConfirmCode-"):
        code = data.split("-", 1)[1]
        await confirm_auto_api_code(chat_id, m_id, code, True)
    
    elif data == "EnterNewCode":
        await app.edit_message_text(
            chat_id, m_id,
            "**لطفا کد تأیید جدید را وارد کنید:**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("(🔙) لغو", callback_data="InstallSelf")]
            ])
        )
        
        update_data(f"UPDATE user SET step = 'EnterNewCode' WHERE id = '{chat_id}'")
    
    elif data.startswith("ShowAPIDetails-"):
        code = data.split("-", 1)[1]
        
        user_info = get_data(f"SELECT phone, api_id, api_hash FROM user WHERE id = '{chat_id}' LIMIT 1")
        
        if not user_info:
            await app.edit_message_text(
                chat_id, m_id,
                "**• اطلاعات کاربر یافت نشد. لطفا مجددا تلاش کنید.**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("(🔙) بازگشت", callback_data="InstallSelf")]
                ])
            )
            return
        
        api_id = user_info.get('api_id')
        api_hash = user_info.get('api_hash')
        
        if not api_id or not api_hash or api_id == 'None' or api_hash == 'None':
            await app.edit_message_text(
                chat_id, m_id,
                "**• API اطلاعات دریافت نشده. لطفا مجددا مراحل را تکرار کنید.**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("(🔙) بازگشت", callback_data="InstallSelf")]
                ])
            )
            return
        
        phone = user_info.get('phone', 'ندارد')
        
        if api_hash and len(api_hash) >= 8:
            masked_hash = f"{api_hash[:4]}{'*' * (len(api_hash)-8)}{api_hash[-4:]}"
        else:
            masked_hash = api_hash
        
        message = f"""**
    📞 Number : `{phone}`
    🆔 Api ID : `{api_id}`
    🆔 Api Hash : `{masked_hash}`
    
    • آیا اطلاعات را تایید میکنید؟                       **"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("بله (✅)", callback_data="ConfirmInstall"),
             InlineKeyboardButton("خیر (❎)", callback_data="ChangeInfo")],
            [InlineKeyboardButton("(🔙) بازگشت", callback_data="Back")]
        ])
        
        await app.edit_message_text(
            chat_id,
            m_id,
            message,
            reply_markup=keyboard
        )
        
        update_data(f"UPDATE user SET step = 'api_confirmation' WHERE id = '{chat_id}'")
    
    elif data == "ToggleGateway":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            current_status = get_gateway_status()
            new_status = not current_status.get("active", False)
        
            merchant_id = current_status.get("merchant_id", "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
            sandbox = current_status.get("sandbox", True)
        
            success = update_gateway_settings("zarinpal", merchant_id, sandbox, new_status)
        
            if success:
                status_text = "فعال شد ✔️" if new_status else "غیرفعال شد ✖️"
                await app.edit_message_text(
                    chat_id, m_id,
                    f"**• وضعیت درگاه زرین پال {status_text}**",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("(🔙) بازگشت", callback_data="GatewaySettings")]
                    ])
                )
            else:
                await app.answer_callback_query(call.id, text="خطا در به روزرسانی تنظیمات", show_alert=True)

    elif data == "EditMerchantID":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            await app.edit_message_text(
                chat_id, m_id,
                "**• لطفا کلید `Api` درگاه خود را ارسال کنید:**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("(🔙) بازگشت", callback_data="GatewaySettings")]
                ])
            )
            update_data(f"UPDATE user SET step = 'edit_merchant_id' WHERE id = '{chat_id}' LIMIT 1")

    elif data == "ToggleSandbox":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            current_status = get_gateway_status()
            new_sandbox = not current_status.get("sandbox", True)
            is_active = current_status.get("active", False)
            merchant_id = current_status.get("merchant_id", "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        
            success = update_gateway_settings("zarinpal", merchant_id, new_sandbox, is_active)
        
            if success:
                sandbox_text = "فعال شد." if new_sandbox else "غیرفعال شد."
                await app.edit_message_text(
                    chat_id, m_id,
                    f"**• حالت درگاه {sandbox_text}**",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("(🔙) بازگشت", callback_data="GatewaySettings")]
                    ])
                )
            else:
                await app.answer_callback_query(call.id, text="خطا در تغییر حالت درگاه", show_alert=True)
    
    elif data == "GatewaySettings":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            gateway_status = get_gateway_status()
        
            status_text = "فعال ✔️" if gateway_status["active"] else "غیرفعال ✖️"
            sandbox_text = "فعال ✔️" if gateway_status.get("sandbox") else "غیرفعال ✖️"
        
            gateway_message = f"""
❁ پرداخت انلاین درگاه :

• **وضعیت درگاه:** {status_text}
• **حالت تست:** {sandbox_text}
• **مرچنت کد:** `{gateway_status.get('merchant_id', 'تنظیم نشده')}`

لطفا گزینه مورد نظر را انتخاب کنید:
"""
        
            keyboard = [
                [InlineKeyboardButton("فعال/غیرفعال درگاه", callback_data="ToggleGateway")],
                [InlineKeyboardButton("تغییر مرچنت کد", callback_data="EditMerchantID")],
                [InlineKeyboardButton("حالت تست", callback_data="ToggleSandbox")],
                [InlineKeyboardButton("مشاهده تراکنش‌ها", callback_data="ViewTransactions")],
                [InlineKeyboardButton("(🔙) بازگشت", callback_data="AdminSettings")]
            ]
        
            await app.edit_message_text(chat_id, m_id, gateway_message, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == "PhoneRestriction":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
                current_status = get_setting("phone_restriction", "enabled")
                status_text = "فعال ✔️" if current_status == "enabled" else "غیرفعال ✖️"
        
                await app.edit_message_text(chat_id, m_id,
                    f"**• محدودیت شماره مجازی\n• وضعیت فعلی : ( {status_text} )\n\nدر صورت فعال بودن این بخش، فقط کاربران ایرانی میتوانند احراز هویت و سلف نصب کنند.**",
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("فعال (✔️)", callback_data="EnablePhoneRestriction"),
                            InlineKeyboardButton("غیرفعال (✖️)", callback_data="DisablePhoneRestriction")
                        ],
                        [InlineKeyboardButton("(🔙) بازگشت", callback_data="AdminSettings")]
                    ]))

    elif data == "EnablePhoneRestriction":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            update_setting("phone_restriction", "enabled")
            await app.edit_message_text(chat_id, m_id,
                "**• قفل شماره مجازی قعال شد✔️**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("(🔙) بازگشت", callback_data="PhoneRestriction")]
                ]))

    elif data == "DisablePhoneRestriction":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            update_setting("phone_restriction", "disabled")
            await app.edit_message_text(chat_id, m_id,
                "**• قفل شماره مجازی غیرفعال شد✔️**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("(🔙) بازگشت", callback_data="PhoneRestriction")]
                ]))
    
    elif data == "SelfStatus":
        if expir > 0:
            user_folder = f"selfs/self-{chat_id}"
            if not os.path.isdir(user_folder):
                await app.edit_message_text(chat_id, m_id,
                    "**• ربات دستیار شما نصب نشده است، ابتدا ربات را نصب کرده و در صورت ایجاد مشکل به این بخش مراجعه کنید.**",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(text="نصب سلف", callback_data="InstallSelf")],
                        [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="Back")]
                    ]))
                return
            
            await app.edit_message_text(chat_id, m_id, 
                "**• درخواست شما به سرور ارسال شد، لطفا کمی صبر کنید.**")
            
            await asyncio.sleep(3.5)
            
            status_info = await check_self_status(chat_id)
            
            if status_info["status"] == "not_installed":
                await app.edit_message_text(chat_id, m_id,
                    "**• ربات دستیار شما نصب نشده است، ابتدا ربات را نصب کرده و در صورت ایجاد مشکل به این بخش مراجعه کنید.**",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(text="نصب سلف", callback_data="InstallSelf")],
                        [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="Back")]
                    ]))
                return
            elif status_info["status"] == "error":
                await app.edit_message_text(chat_id, m_id,
                    "**• خطا در بررسی وضعیت سلف.**\n\n"
                    f"{status_info['message']}\n\n"
                    "لطفا با پشتیبانی در ارتباط باشید یا مجدداً سلف را نصب کنید.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="Back")]
                    ]))
                return
            elif status_info["status"] == "inactive":
                await app.edit_message_text(chat_id, m_id,
                    "**• ربات دستیار شما نصب نشده است، ابتدا ربات را نصب کرده و در صورت ایجاد مشکل به این بخش مراجعه کنید.**",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(text="نصب سلف", callback_data="InstallSelf")],
                        [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="Back")]
                    ]))
                return
            else:
                status_message = (
                    f"**درخواست شما با موفقیت انجام شد.**\n\n"
                    f"**نتیجه:** {status_info['message']}\n\n"
                )
                
                if status_info["language"]:
                    status_message += f"**توجه: دستیار شما روی زبان {status_info['language']} تنظیم شده و فقط به دستورات با این زبان پاسخ خواهد داد.**"
                
                await app.edit_message_text(chat_id, m_id, status_message,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="Back")]
                    ]))
        else:
            await app.answer_callback_query(call.id, text="• شما انقضا ندارید •", show_alert=True)
    
    elif data == "ChangeLang":
        if expir > 0:
            can_change, remaining = can_change_language(chat_id)
            
            if not can_change:
                await app.edit_message_text(call.from_user.id, m_id, 
                    f"**• شما به تازگی زبان دستیار خود را تعویض کرده اید و نا ( `{remaining}` ) دقیقه دیگر محدودیت به سر میبرید.**")
                return
            
            current_lang = get_current_language(chat_id)
            
            next_lang = "en" if current_lang == "fa" else "fa"
            next_lang_display = "انگلیسی" if next_lang == "en" else "فارسی"
            current_lang_display = "فارسی 🇮🇷" if current_lang == "fa" else "انگلیسی 🇬🇧"
            
            await app.edit_message_text(chat_id, m_id,
                f"**• زبان دستیار شما درحال حاظر روی ( {current_lang_display} ) تنظیم شده.\n  » آیا مطمئن هستید که میخواهید زبان دستیار خود را به {next_lang_display} تغییر دهید؟**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="بله ✔️", callback_data=f"ConfirmLangChange-{next_lang}"),
                     InlineKeyboardButton(text="خیر ✖️", callback_data="Back")]
                ]))
        else:
            await app.answer_callback_query(call.id, text="• شما انقضا ندارید •", show_alert=True)
    
    elif data.startswith("ConfirmLangChange-"):
        target_lang = data.split("-")[1]
        
        success, result = await change_self_language(chat_id, target_lang)
        
        if success:
            new_lang_display = "فارسی 🇮🇷" if target_lang == "fa" else "انگلیسی 🇬🇧"
            
            await app.edit_message_text(chat_id, m_id,
                "**• درخواست شما به سرور ارسال شد ، صبر کنید.**"
            )
            await asyncio.sleep(2.5)
            await app.edit_message_text(chat_id, m_id,
                f"**• زبان دستیار شما روی ( {new_lang_display} ) تنظیم شد.**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="Back")]
                ]))
            
            user_data = get_data(f"SELECT pid FROM user WHERE id = '{chat_id}' LIMIT 1")
            pid = user_data.get("pid") if user_data else None
            
            if pid:
                try:
                    os.kill(pid, signal.SIGTERM)
                    await asyncio.sleep(3)
                    
                    try:
                        os.kill(pid, 0)
                        os.kill(pid, signal.SIGKILL)
                    except OSError:
                        pass
                        
                except Exception as e:
                    pass
        else:
            await app.edit_message_text(chat_id, m_id,
                f"**• عملیات کنسل شد، با پشتیبانی در ارتباط باشید.***",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="Back")]
                ]))
    
    elif data == "AdminCreateCode":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            await app.edit_message_text(chat_id, m_id,
                "**لطفا تعداد روز انقضای کد را وارد کنید:**",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]
                    ]))
            update_data(f"UPDATE user SET step = 'admin_create_code_days' WHERE id = '{chat_id}' LIMIT 1")

    elif data == "AdminListCodes":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            cleanup_inactive_codes()
            
            codes = get_active_codes()
            
            if codes:
                codes_text = "**• لیست کدهای فعال :\n\n"
                for idx, code in enumerate(codes, 1):
                    codes_text += f"**{idx} - کد : ( `{code['code']}` )**\n"
                    codes_text += f"**• روزهای انقضا : ( {code['days']} روز )**\n"
                    codes_text += f"**• تاریخ ایجاد : ( {code['created_at']} )**\n\n"
                
                await app.edit_message_text(chat_id, m_id, codes_text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]
                    ]))
            else:
                await app.edit_message_text(chat_id, m_id,
                    "**هیچ کد فعالی وجود ندارد.**",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]
                        ]))

    elif data == "AdminDeleteCode":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            codes = get_active_codes()
            
            if codes:
                keyboard_buttons = []
                for code in codes:
                    keyboard_buttons.append([
                        InlineKeyboardButton(text=f"• {code['code']}", callback_data=f"DeleteCode-{code['id']}")
                    ])
                keyboard_buttons.append([InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")])
                
                await app.edit_message_text(chat_id, m_id,
                    "**لطفا کدی که می خواهید حذف کنید را انتخاب کنید:**",
                    reply_markup=InlineKeyboardMarkup(keyboard_buttons))
            else:
                await app.answer_callback_query(call.id, text="• کد فعالی وجود ندارد •", show_alert=True)

    elif data.startswith("DeleteCode-"):
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            code_id = data.split("-")[1]
            delete_code(code_id)
            await app.edit_message_text(chat_id, m_id,
                "**کد با موفقیت حذف شد.**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="DeleteCode-")]
                ]))
    
    elif data == "BuyCode":
        await app.edit_message_text(chat_id, m_id,
            "**• لطفا کد انقضای خریداری شده خود را ارسال کنید:**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="Back")]
            ]))
        update_data(f"UPDATE user SET step = 'use_code' WHERE id = '{call.from_user.id}' LIMIT 1")
        
    elif data == "AdminSettings":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            await app.edit_message_text(chat_id, m_id,
                "**مدیر گرامی، به بخش تنظیمات خوش آمدید.\nلطفا گزینه مورد نظر را انتخاب کنید:**",
                reply_markup=AdminSettingsKeyboard)
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

    elif data == "EditStartMessage":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            current_message = get_setting("start_message")
            await app.edit_message_text(chat_id, m_id,
                f"**متن فعلی پیام استارت:**\n\n{current_message}\n\n**لطفا متن جدید را ارسال کنید:**\n\n**نکته:** برای نمایش نام کاربر میتوانید از `{{user_link}}` استفاده کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminSettings")]
                ]))
            update_data(f"UPDATE user SET step = 'edit_start_message' WHERE id = '{chat_id}' LIMIT 1")

    elif data == "EditPriceMessage":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            current_message = get_setting("price_message")
            await app.edit_message_text(chat_id, m_id,
                f"**متن فعلی پیام نرخ:**\n\n{current_message}\n\n**لطفا متن جدید را ارسال کنید:**\n\n**نکته:** برای نمایش قیمت‌ها میتوانید از متغیرهای زیر استفاده کنید:\n- `{{price_1month}}`\n- `{{price_2month}}`\n- `{{price_3month}}`\n- `{{price_4month}}`\n- `{{price_5month}}`\n- `{{price_6month}}`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminSettings")]
                ]))
            update_data(f"UPDATE user SET step = 'edit_price_message' WHERE id = '{chat_id}' LIMIT 1")

    elif data == "EditSelfMessage":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            current_message = get_setting("whatself_message")
            await app.edit_message_text(chat_id, m_id,
                f"**متن فعلی توضیح سلف:**\n\n{current_message}\n\n**لطفا متن جدید را ارسال کنید:**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminSettings")]
                ]))
            update_data(f"UPDATE user SET step = 'edit_self_message' WHERE id = '{chat_id}' LIMIT 1")

    elif data == "EditPrices":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            f"**لطفا نرخ موردنظر خودتون رو به صورت زیر وارد کنید.\n( به صورت خط به خط ، خط اول نزخ یک ماهه، خط دوم نرخ دو ماهه و به همین صورت تا نرخ 6 ماهه )\n\n100000\n200000\n300000\n400000\n500000\n600000**"
    
            await app.edit_message_text(chat_id, m_id, prices_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminSettings")]
                ]))
            update_data(f"UPDATE user SET step = 'edit_all_prices' WHERE id = '{chat_id}' LIMIT 1")

    elif data == "EditCardInfo":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            current_card = get_setting("card_number")
            current_name = get_setting("card_name")
        
            await app.edit_message_text(chat_id, m_id,
                f"**• اطلاعات پرداخت :\nنام مالک کارت : ( `{current_name}` )\nشماره کارت : ( `{current_card}` )**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="تغییر شماره کارت", callback_data="EditCardNumber")],
                    [InlineKeyboardButton(text="تغییر نام صاحب کارت", callback_data="EditCardName")],
                    [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminSettings")]
                ]))

    elif data == "EditCardNumber":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            current_card = get_setting("card_number")
            await app.edit_message_text(chat_id, m_id,
                f"**شماره کارت فعلی : ( `{current_card}` )\n\n• لطفا شماره کارت جدید را وارد کنید:**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="EditCardInfo")]
                ]))
            update_data(f"UPDATE user SET step = 'edit_card_number' WHERE id = '{chat_id}' LIMIT 1")

    elif data == "EditCardName":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            current_name = get_setting("card_name")
            await app.edit_message_text(chat_id, m_id,
                f"**نام صاحب کارت فعلی : ( {current_name} )\n\n• لطفا نام جدید را وارد کنید:**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="EditCardInfo")]
                ]))
            update_data(f"UPDATE user SET step = 'edit_card_name' WHERE id = '{chat_id}' LIMIT 1")

    elif data == "ViewSettings":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            settings = get_all_settings()
            settings_text = "**تنظیمات فعلی ربات:**\n\n"
            for setting in settings:
                key = setting[1]
                value = setting[2][:50] + "..." if len(str(setting[2])) > 50 else setting[2]
                desc = setting[3]
                settings_text += f"**{desc}:**\n`{key}` = `{value}`\n\n"
        
            await app.edit_message_text(chat_id, m_id, settings_text,
                                   reply_markup=InlineKeyboardMarkup([
                                       [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminSettings")]
                                   ]))
    
    elif data == "InstallSelf":
        if expir > 0:
            user_info = get_data(f"SELECT phone FROM user WHERE id = '{chat_id}' LIMIT 1")
            
            if user_info and user_info["phone"]:
                await app.edit_message_text(
                    chat_id, m_id,
                    f"**» لطفا انتخاب کنید:\n**"
                    f"**میخواهید به صورت دستی Api Id , Hash را وارد کنید یا ربات به صورت خودکار این کار را انجام دهد؟\n\n**"
                    "‌‌‌‌ ‌           ‌‌‌‌ ",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("دستی 👤", callback_data="ManualInstall"),
                        InlineKeyboardButton("خودکار 🤖", callback_data="AutoInstall")],
                        [InlineKeyboardButton("(🔙) بازگشت", callback_data="Back")]
                    ])
                )
                update_data(f"UPDATE user SET step = 'select_install_method' WHERE id = '{chat_id}' LIMIT 1")
            else:
                await app.edit_message_text(
                    chat_id, m_id,
                    "**برای نصب سلف، لطفا شماره تلفن خود را با دکمه زیر به اشتراک بگذارید:**",
                    reply_markup=ReplyKeyboardMarkup(
                        [[KeyboardButton(text="اشتراک گذاری شماره", request_contact=True)]],
                        resize_keyboard=True
                    )
                )
                update_data(f"UPDATE user SET step = 'install_phone' WHERE id = '{chat_id}' LIMIT 1")
        else:
            await app.send_message(chat_id, "**شما انقضا ندارید.**")

    elif data == "ManualInstall":
        user_info = get_data(f"SELECT phone FROM user WHERE id = '{chat_id}' LIMIT 1")
        
        if user_info and user_info["phone"]:
            await app.edit_message_text(
                chat_id, m_id,
                "**لطفا `Api Id` خود را ارسال کنید. ( نمونه : 123456 )\n\n• لغو عملیات [ /start ]**"
            )
            update_data(f"UPDATE user SET step = 'install_api_id' WHERE id = '{chat_id}'")
        else:
            await app.answer_callback_query(call.id, text="• شماره تلفن ثبت نشده است •", show_alert=True)

    elif data == "AutoInstall":
        user_info = get_data(f"SELECT phone FROM user WHERE id = '{chat_id}' LIMIT 1")
        
        if user_info and user_info["phone"]:
            phone = user_info["phone"]
            
            await app.edit_message_text(
                chat_id, m_id,
                "**• عملیات دریافت درحال شروع میباشد ، لطفا صبر کنید.**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("(🔙) بازگشت", callback_data="InstallSelf")]
                ])
            )
            
            result = await process_auto_api(chat_id, phone)
            
            if result["success"] and result.get("requires_code"):
                update_data(f"""
                    UPDATE user SET 
                    step = 'awaiting_code_confirmation-{phone}'
                    WHERE id = '{chat_id}'
                """)
                
                await app.edit_message_text(
                    chat_id, m_id,
                    "**• لطفا کد ارسال شده توسط تلگرام را وارد کنید.**",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("• بازگشت •", callback_data="InstallSelf")]
                    ])
                )
            elif result["success"]:
                # اگر API اطلاعات دریافت شده
                if "api_id" in result and "api_hash" in result:
                    # ذخیره در دیتابیس
                    update_data(f"""
                        UPDATE user SET 
                        api_id = '{result['api_id']}',
                        api_hash = '{result['api_hash']}',
                        step = 'api_received-{result['api_id']}-{result['api_hash']}'
                        WHERE id = '{chat_id}'
                    """)
                    
                    # نمایش اطلاعات
                    masked_hash = f"{result['api_hash'][:4]}{'*' * (len(result['api_hash'])-8)}{result['api_hash'][-4:]}"
                    
                    await app.edit_message_text(
                        chat_id, m_id,
                        f"**📞 Number : `{phone}`\n"
                        f"🆔 Api ID : `{result['api_id']}`\n"
                        f"🆔 Api Hash : `{masked_hash}`\n\n"
                        f"• آیا اطلاعات را تایید میکنید؟**",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("بله (✅)", callback_data="ConfirmInstall"),
                             InlineKeyboardButton("خیر (❎)", callback_data="ChangeInfo")],
                            [InlineKeyboardButton("(🔙) بازگشت", callback_data="Back")]
                        ])
                    )
                else:
                    await app.edit_message_text(
                        chat_id, m_id,
                        "**• عملیات موفق بود اما API اطلاعات دریافت نشد.**",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("(🔙) بازگشت", callback_data="InstallSelf")]
                        ])
                    )
            else:
                await app.edit_message_text(
                    chat_id, m_id,
                    f"**عملیات با خطا مواجه شد.**\n```\n{result['message']}\n```",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("(🔙) بازگشت", callback_data="InstallSelf")]
                    ])
                )
        else:
            await app.answer_callback_query(call.id, text="• شماره تلفن ثبت نشده •", show_alert=True)

    elif data.startswith("ConfirmAutoInstall-"):
        parts = data.split("-")
        if len(parts) >= 3:
            api_id = parts[1]
            api_hash = parts[2]
            
            # ذخیره در دیتابیس
            update_data(f"""
                UPDATE user SET 
                api_id = '{api_id}',
                api_hash = '{api_hash}'
                WHERE id = '{chat_id}'
            """)
            
            user_info = get_data(f"SELECT phone FROM user WHERE id = '{chat_id}' LIMIT 1")
            
            if user_info and user_info["phone"]:
                masked_hash = f"{api_hash[:4]}{'*' * (len(api_hash)-8)}{api_hash[-4:]}"
                
                await app.edit_message_text(
                    chat_id,
                    m_id,
                    "**• زبان سلف را انتخاب کنید:**",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("فارسی 🇮🇷", callback_data=f"SelectLanguageAuto-fa-{api_id}-{api_hash}"),
                         InlineKeyboardButton("English 🇬🇧", callback_data=f"SelectLanguageAuto-en-{api_id}-{api_hash}")]
                    ])
                )
        else:
            await app.answer_callback_query(call.id, text="• اطلاعات نامعتبر •", show_alert=True)

    elif data.startswith("SelectLanguageAuto-"):
        parts = data.split("-")
        if len(parts) >= 4:
            target_language = parts[1]
            api_id = parts[2]
            api_hash = parts[3]
            
            user_info = get_data(f"SELECT phone FROM user WHERE id = '{chat_id}' LIMIT 1")
            
            if user_info and user_info["phone"]:
                phone = user_info["phone"]
                
                await app.edit_message_text(chat_id, m_id, "**• درحال ساخت سلف، لطفا صبور باشید.**")
                
                success = await start_self_installation(chat_id, phone, api_id, api_hash, m_id, target_language)
                
                if not success:
                    await app.edit_message_text(
                        chat_id, m_id,
                        "**خطا در نصب!**",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("📞 پشتیبانی", callback_data="Support")]
                        ])
                    )
        else:
            await app.answer_callback_query(call.id, text="• اطلاعات نامعتبر •", show_alert=True)
    
    elif data == "ConfirmInstall":
        user_info = get_data(f"SELECT phone, api_id, api_hash FROM user WHERE id = '{chat_id}' LIMIT 1")
        if user_info and user_info["phone"] and user_info["api_id"] and user_info["api_hash"]:
            await app.edit_message_text(chat_id, m_id,
                "**• زبان سلف را انتخاب کنید.**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("فارسی 🇮🇷", callback_data=f"SelectLanguage-fa"),
                    InlineKeyboardButton("English 🇬🇧", callback_data=f"SelectLanguage-en")],
                    [InlineKeyboardButton("(🔙) بازگشت", callback_data="Back")]
                ]))
            update_data(f"UPDATE user SET step = 'select_language-{user_info['phone']}-{user_info['api_id']}-{user_info['api_hash']}' WHERE id = '{chat_id}' LIMIT 1")
        else:
            await app.answer_callback_query(call.id, text="• اطلاعات شما ناقص است •", show_alert=True)

    elif data.startswith("SelectLanguage-"):
        target_language = data.split("-")[1]
        user_step = user["step"]
    
        if user_step.startswith("select_language-"):
            parts = user_step.split("-", 1)
            if len(parts) > 1:
                remaining_parts = parts[1]
                update_data(f"UPDATE user SET step = 'install_with_language-{remaining_parts}-{target_language}' WHERE id = '{chat_id}' LIMIT 1")
            
                remaining_parts_parts = remaining_parts.split("-")
                if len(remaining_parts_parts) >= 3:
                    phone = remaining_parts_parts[0]
                    api_id = remaining_parts_parts[1]
                    api_hash = remaining_parts_parts[2]
                
                    await app.edit_message_text(chat_id, m_id, "**• درحال ساخت سلف، لطفا صبور باشید.**")
                
                    await start_self_installation(chat_id, phone, api_id, api_hash, m_id, target_language)

    elif data == "ChangeInfo":
        await app.edit_message_text(chat_id, m_id,
            "**لطفا شماره تلفن خود را با دکمه زیر به اشتراک بگذارید:**",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton(text="اشتراک گذاری شماره", request_contact=True)]],
                resize_keyboard=True
            ))
        update_data(f"UPDATE user SET step = 'install_phone' WHERE id = '{chat_id}' LIMIT 1")

    elif data == "StartInstallation":
        user_info = get_data(f"SELECT phone, api_id, api_hash FROM user WHERE id = '{chat_id}' LIMIT 1")
        if user_info and user_info["phone"] and user_info["api_id"] and user_info["api_hash"]:
            await app.edit_message_text(chat_id, m_id, "**• درحال ساخت سلف، لطفا صبور باشید.**")
            await start_self_installation(chat_id, user_info["phone"], user_info["api_id"], user_info["api_hash"])
        else:
            await app.answer_callback_query(call.id, text="• اطلاعات شما ناقص است •", show_alert=True)
    
    elif data == "ExpiryStatus":
        await app.answer_callback_query(call.id, text=f"انقضای شما : ( {expir} روز )", show_alert=True)

    elif data == "AdminPanel":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            await app.edit_message_text(chat_id, m_id, "**• به پنل مدیریت خوش آمدید ، انتخاب کنید:**", reply_markup=AdminPanelKeyboard)
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
            async with lock:
                if chat_id in temp_Client:
                    del temp_Client[chat_id]
        else:
            await app.answer_callback_query(call.id, text="**شما دسترسی به بخش مدیریت ندارید.**", show_alert=True)
    
    elif data == "AdminStats":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            botinfo = await app.get_me()
            allusers = get_datas("SELECT COUNT(id) FROM user")[0][0]
            allblocks = get_datas("SELECT COUNT(id) FROM block")[0][0]
            pending_cards = len(get_pending_cards())
            
            await app.edit_message_text(chat_id, m_id, f"""
            • تعداد کل کاربران ربات : **[ {allusers} ]**
            • تعداد کاربران بلاک شده :  **[ {allblocks} ]**
            • تعداد کارت های در انتضار تایید : **[ {pending_cards} ]**
            
            • نام ربات : **( {botinfo.first_name} )**
            • آیدی عددی ربات : **( `{botinfo.id}` )**
            • آیدی ربات : **( @{botinfo.username} )**
            """, reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
            ))
    
    elif data == "AdminBroadcast":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            await app.edit_message_text(chat_id, m_id, f"**پیام خود را جهت ارسال همگانی، ارسال کنید.**\n\n• با ارسال پیام در این بخش، پیام شما برای تمامی کاربران ربات **ارسال** میشود.", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
            ))
            update_data(f"UPDATE user SET step = 'admin_broadcast' WHERE id = '{chat_id}' LIMIT 1")
    
    elif data == "AdminForward":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            await app.edit_message_text(chat_id, m_id, f"**پیام خود را جهت فوروارد همگانی ارسال کنید.**\n\n• با ارسال پیام در این بخش، پیام شما برای تمامی کاربران ربات **فوروارد** میشود.", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
            ))
            update_data(f"UPDATE user SET step = 'admin_forward' WHERE id = '{chat_id}' LIMIT 1")
    
    elif data == "AdminBlock":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            await app.edit_message_text(chat_id, m_id, "**آیدی عددی کاربر را جهت مسدود از ربات ارسال کنید:**", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
            ))
            update_data(f"UPDATE user SET step = 'admin_block' WHERE id = '{chat_id}' LIMIT 1")
    
    elif data == "AdminUnblock":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            await app.edit_message_text(chat_id, m_id, "**آیدی عددی کاربر را جهت پاک کردن از لیست مسدود ها ارسال کنید:**", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
            ))
            update_data(f"UPDATE user SET step = 'admin_unblock' WHERE id = '{chat_id}' LIMIT 1")
    
    elif data == "AdminAddExpiry":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            await app.edit_message_text(chat_id, m_id, "**• آیدی عددی کاربر را جهت افزایش انقضا ارسال کنید:**", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
            ))
            update_data(f"UPDATE user SET step = 'admin_add_expiry1' WHERE id = '{chat_id}' LIMIT 1")
    
    elif data == "AdminDeductExpiry":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            await app.edit_message_text(chat_id, m_id, "**• آیدی عددی کاربر را جهت کسر انقضا ارسال کنید:**", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
            ))
            update_data(f"UPDATE user SET step = 'admin_deduct_expiry1' WHERE id = '{chat_id}' LIMIT 1")
    
    elif data == "AdminActivateSelf":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            await app.edit_message_text(chat_id, m_id, "**آیدی عددی کاربر را جهت فعالسازی سلف ارسال کنید:**", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
            ))
            update_data(f"UPDATE user SET step = 'admin_activate_self' WHERE id = '{chat_id}' LIMIT 1")
    
    elif data == "AdminDeactivateSelf":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            await app.edit_message_text(chat_id, m_id, "**آیدی عددی کاربر را جهت غیرفعال سازی سلف ارسال کنید:**", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
            ))
            update_data(f"UPDATE user SET step = 'admin_deactivate_self' WHERE id = '{chat_id}' LIMIT 1")
    
    elif data == "AdminTurnOn":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            bot = get_data("SELECT * FROM bot")
            if bot["status"] != "ON":
                await app.edit_message_text(chat_id, m_id, "**• ربات روشن شد.**", reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                ))
                update_data(f"UPDATE bot SET status = 'ON' LIMIT 1")
            else:
                await app.answer_callback_query(call.id, text="**• ربات روشن بوده است.**", show_alert=True)
    
    elif data == "AdminTurnOff":
        if call.from_user.id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1") is not None:
            bot = get_data("SELECT * FROM bot")
            if bot["status"] != "OFF":
                await app.edit_message_text(chat_id, m_id, "**• ربات خاموش شد.**", reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                ))
                update_data(f"UPDATE bot SET status = 'OFF' LIMIT 1")
            else:
                await app.answer_callback_query(call.id, text="**• ربات خاموش بوده است.**", show_alert=True)
    
    elif data.startswith("AdminVerifyCard-"):
        params = data.split("-")
        user_id = int(params[1])
        card_number = params[2]
    
        bank_name = detect_bank(card_number)
        card = get_card_by_number(user_id, card_number)
    
        if card:
            update_card_status(card["id"], "verified", bank_name)
    
        user_info = await app.get_users(user_id)
        username = f"@{user_info.username}" if user_info.username else "ندارد"
    
        await app.edit_message_text(call.message.chat.id, call.message.id, f"""**• درخواست احراز هویت از طرف ( {html.escape(user_info.first_name)} - {username} - {user_id} )
• شماره کارت : [ {card_number} ]

به دستور ( {call.from_user.id} ) تایید شد.**""")
    
        await app.send_message(user_id, f"**• درخواست احراز هویت کارت ( `{card_number}` ) تایید شد.\nشما هم اکنون میتوانید از بخش خرید / تمدید اشتراک ، خرید خود را انجام دهید.**")

    elif data.startswith("AdminRejectCard-"):
        params = data.split("-")
        user_id = int(params[1])
        card_number = params[2]
    
        card = get_card_by_number(user_id, card_number)
        if card:
            update_card_status(card["id"], "rejected")
        user_info = await app.get_users(user_id)
        username = f"@{user_info.username}" if user_info.username else "ندارد"
    
        await app.edit_message_text(call.message.chat.id, call.message.id, f"""**• درخواست احراز هویت از طرف ( {html.escape(user_info.first_name)} - {username} - {user_id} )
• شماره کارت : [ {card_number} ]

به دستور ( {call.from_user.id} ) رد شد.**""")
    
        await app.send_message(user_id, f"**• درخواست احراز هویت کارت ( {card_number} ) به دلیل اشتباه بودن، رد شد.\nشما میتوانید مجددا برای احراز هویت با رعایت شرایط، درخواست دهید.**")

    elif data.startswith("AdminIncompleteCard-"):
        params = data.split("-")
        user_id = int(params[1])
        card_number = params[2]
    
        card = get_card_by_number(user_id, card_number)
        if card:
            update_card_status(card["id"], "rejected")
        user_info = await app.get_users(user_id)
        username = f"@{user_info.username}" if user_info.username else "ندارد"
    
        await app.edit_message_text(call.message.chat.id, call.message.id, f"""**• درخواست احراز هویت از طرف ( {html.escape(user_info.first_name)} - {username} - {user_id} )
• شماره کارت : [ {card_number} ]

به دستور ( {call.from_user.id} ) رد شد.**""")
    
        await app.send_message(user_id, f"**• درخواست احراز هویت کارت ( {card_number} ) به دلیل ناقص بودن ، رد شد.\nشما میتوانید مجددا برای احراز هویت با رعایت شرایط، درخواست دهید.**")
    
    elif data.startswith("AdminApprovePayment-"):
        params = data.split("-")
        user_id = int(params[1])
        expir_count = int(params[2])
        cost = params[3]
        transaction_id = params[4]
        
        user_data = get_data(f"SELECT expir FROM user WHERE id = '{user_id}' LIMIT 1")
        old_expir = user_data["expir"] if user_data else 0
        new_expir = old_expir + expir_count
        
        update_data(f"UPDATE user SET expir = '{new_expir}' WHERE id = '{user_id}' LIMIT 1")
        
        if expir_count == 31:
            month_text = "یک ماه"
        elif expir_count == 62:
            month_text = "دو ماه"
        elif expir_count == 93:
            month_text = "سه ماه"
        elif expir_count == 124:
            month_text = "چهار ماه"
        elif expir_count == 155:
            month_text = "پنج ماه"
        elif expir_count == 186:
            month_text = "شش ماه"
        else:
            month_text = f"{expir_count} روز"
        
        await app.edit_message_text(Admin, m_id, f"**پرداخت کاربر [ `{user_id}` ] تایید شد.\n\n• شناسه تراکنش : ( `{transaction_id}` )\n• انقضای جدید کاربر : ( `{new_expir} روز` )**")
        
        await app.send_message(user_id, f"**پرداخت شما تایید شد.\n• شناسه تراکنش : ( {transaction_id} )\n• انقضای سلف شما {month_text} اضافه گردید.\n\nانقضای قبلی شما : ( `{old_expir}` روز )\n\n• انقضای جدید : ( `{new_expir}` روز )**")
    
    elif data.startswith("AdminRejectPayment-"):
        params = data.split("-")
        user_id = int(params[1])
        transaction_id = params[2]
        
        await app.edit_message_text(Admin, m_id,f"**• پرداخت کاربر [ `{user_id}` ] رد شد.**")
        
        await app.edit_message_text(user_id, f"**پرداخت شما رد گردید.\n\n•شناسه تراکنش : ( `{transaction_id}` )\n• افزایش انقضای شما به دلیل ارسال فیش واربزی اشتباه رد شده و درخواست شما لغو گردید.\n• در صورتی که غکر میکنید اشتباه شده است، شناسه تراکنش را به پشتیبانی ارسال کرده و با پشتیان ها در ارتباط باشید.**")
    
    elif data.startswith("AdminBlockPayment-"):
        user_id = int(data.split("-")[1])
        
        update_data(f"INSERT INTO block(id) VALUES({user_id})")
        
        await app.edit_message_text(Admin, m_id, f"**• کاربر [ `{user_id}` ] از ربات مسدود شد.**")
        
        await app.send_message(user_id, f"**شما به دلیل نقض قوانین از ربات مسدود شده اید.\n• با پشتیبان ها در ارتباط باشید.**")
    
    elif data.startswith("Reply-"):
        user_id = int(data.split("-")[1])
        user_info = await app.get_users(user_id)
        await app.edit_message_text(
            Admin,
            m_id,
            f"**• پیام خود را جهت پاسخ به کاربر [ {html.escape(user_info.first_name)} ] ارسال کنید:**",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
            )
        )
        update_data(f"UPDATE user SET step = 'ureply-{user_id}' WHERE id = '{Admin}' LIMIT 1")

    elif data.startswith("Block-"):
        user_id = int(data.split("-")[1])
        user_info = await app.get_users(user_id)
        block = get_data(f"SELECT * FROM block WHERE id = '{user_id}' LIMIT 1")
        if block is None:
            await app.send_message(user_id, "**شما به دلیل نقض قوانین از ربات مسدود شدید.**")
            await app.send_message(Admin, f"**• کاربر [ {html.escape(user_info.first_name)} ] از ربات مسدود شد.**")
            update_data(f"INSERT INTO block(id) VALUES({user_id})")
        else:
            await app.send_message(Admin, f"**• کاربر [ {html.escape(user_info.first_name)} ] از قبل بلاک بوده است.**")

    elif data == "Back":
        try:
            chat_id = call.from_user.id
            user_info = get_data(f"SELECT * FROM user WHERE id = {chat_id}")
        
            if not user_info:
                update_data(f"""
                    INSERT INTO user(id, step, expir) 
                    VALUES({chat_id}, 'none', 0)
            """)
                user_info = {"id": chat_id, "expir": 0, "step": "none"}
        
            expir = user_info.get("expir", 0)
            if expir is None:
                expir = 0
        
            is_admin = False
            try:
                admin_check = get_data(f"SELECT * FROM adminlist WHERE id = {chat_id}")
                if admin_check or chat_id == Admin:
                    is_admin = True
            except:
                is_admin = (chat_id == Admin)
        
            has_self_folder = os.path.isdir(f"selfs/self-{chat_id}")
            
            current_lang = "fa"
            keyboard = get_main_keyboard(
                user_id=chat_id,
                expir=expir,
                is_admin=is_admin,
                has_self_folder=has_self_folder,
            current_lang=current_lang
            )
        
            update_data(f"UPDATE user SET step = 'none' WHERE id = {chat_id}")
        
            async with lock:
                if chat_id in temp_Client:
                    try:
                        if temp_Client[chat_id]["client"].is_connected:
                            await temp_Client[chat_id]["client"].disconnect()
                    except:
                        pass
                    del temp_Client[chat_id]
            await app.answer_callback_query(
                call.id,
                text="• به منوی اصلی بازگشتید •",
                show_alert=False
            )
            await app.edit_message_text(
                chat_id,
                call.message.id,
                f"**\n ‌‌‌‌‌ ‌‌‌‌‌‌‌   ‌    ‌‌‌‌‌‌‌ ‌‌‌        ‌‌‌‌‌‌‌‌‌\nبه منوی اصلی بازگشتید.\n\nلطفا اگر سوالی دارید از بخش پشتیبانی ، با پشتیبان ها در ارتباط باشید.\n\n            لطفا انتخاب کنید:\n‌‌‌‌ ‌     ‌‌‌‌‌ ‌‌‌\n ‌    ‌‌‌‌     ‌‌**",
                reply_markup=keyboard
            )
        
        except Exception as e:
            await app.answer_callback_query(
                call.id,
                text="خطا در بازگشت. لطفا /start را بزنید.",
                show_alert=True
            )
    
    elif data == "text":
        await app.answer_callback_query(call.id, text="• دکمه نمایشی است •", show_alert=True)

@app.on_message(filters.private & filters.command("checkcards"))
async def check_cards_command(c, m):
    """بررسی کارت‌های کاربر"""
    if m.chat.id != Admin:
        return
    
    if len(m.text.split()) > 1:
        user_id = int(m.text.split()[1])
    else:
        user_id = m.chat.id
    
    await app.send_message(m.chat.id, f"**در حال بررسی کارت‌های کاربر {user_id}...**")
    
    try:
        # تست مستقیم از دیتابیس
        query = "SELECT * FROM cards WHERE user_id = %s AND verified = 'verified'"
        connection = pymysql.connect(
            host="localhost",
            user=DBUser,
            password=DBPass,
            database=DBName,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            cursor.execute(query, [user_id])
            cards = cursor.fetchall()
            
            if cards:
                message = f"**کارت‌های verified کاربر {user_id}:**\n\n"
                for card in cards:
                    message += f"• **شماره:** `{card['card_number']}`\n"
                    message += f"  **بانک:** `{card.get('bank_name', 'ندارد')}`\n"
                    message += f"  **وضعیت:** `{card['verified']}`\n\n"
            else:
                message = f"**کاربر {user_id} هیچ کارت verified ندارد.**"
            
            await app.send_message(m.chat.id, message)
        
        connection.close()
        
    except Exception as e:
        await app.send_message(m.chat.id, f"**خطا:** `{str(e)[:100]}`")

@app.on_message(filters.private & filters.command("clearcache"))
async def clear_cache_command(c, m):
    """پاک کردن کش"""
    if m.chat.id != Admin:
        return
    
    with _cache_lock:
        _user_cache.clear()
        _settings_cache.clear()
        _file_cache.clear()
        _channel_cache.clear()
        _keyboard_cache.clear()
    
    get_user_cached_lru.cache_clear()
    get_setting.cache_clear()
    get_user_cards.cache_clear()
    
    await m.reply("**✅ تمامی کش‌ها پاک شدند.**")

@app.on_message(filters.contact)
@checker
async def contact_handler(c, m):
    user = get_data(f"SELECT * FROM user WHERE id = '{m.chat.id}' LIMIT 1")
    
    phone_number = str(m.contact.phone_number)
    if not phone_number.startswith("+"):
        phone_number = f"+{phone_number}"
    
    is_valid, error_message = validate_phone_number(phone_number)
    
    if not is_valid:
        await app.send_message(m.chat.id, f"**• {error_message}**")
        return
    
    contact_id = m.contact.user_id
    
    if user["step"] == "install_phone":
        if m.contact and m.chat.id == contact_id:
            update_data(f"UPDATE user SET phone = '{phone_number}' WHERE id = '{m.chat.id}' LIMIT 1")
            
            await app.send_message(m.chat.id, "**شماره شما ثبت شد.", reply_markup=ReplyKeyboardRemove())
            await app.send_message(
                m.chat.id,
                f"**» لطفا انتخاب کنید:\n**"
                f"**میخواهید به صورت دستی Api Id , Hash را وارد کنید یا ربات به صورت خودکار این کار را انجام دهد؟\n\n**‌‌‌‌ ‌           ‌‌‌‌ ",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("دستی 👤", callback_data="ManualInstall"),
                    InlineKeyboardButton("خودکار 🤖", callback_data="AutoInstall")],
                    [InlineKeyboardButton("(🔙) بازگشت", callback_data="Back")]
                ]))
                
            
            update_data(f"UPDATE user SET step = 'select_install_method' WHERE id = '{m.chat.id}' LIMIT 1")
        else:
            await app.send_message(m.chat.id, "** لطفا شماره خود را با دکمه «اشتراک گذاری شماره» ارسال کنید.**")
        return
    
    elif user.get("step") == "contact":
        if m.contact and m.chat.id == contact_id:
            await app.send_message(
                m.chat.id, 
                "**• شماره شما با موفقیت ذخیره شد.**\n"
                "**اکنون می‌توانید از بخش خرید استفاده کنید.**\n\n"
                "**ربات رو مجددا [ /start ] کنید.**", 
                reply_markup=ReplyKeyboardRemove()
            )
            update_data(f"UPDATE user SET phone = '{phone_number}', step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
        else:
            await app.send_message(m.chat.id, "** با استفاده از دکمه « اشتراک گذاری شماره » شماره تلفن را ارسال نمایید.**")

@app.on_message(filters.private & filters.command("cache"))
async def cache_management(c, m):
    if m.chat.id != Admin:
        return
    
    command = m.text.split()[1] if len(m.text.split()) > 1 else "stats"
    
    if command == "clear":
        with _cache_lock:
            _user_cache.clear()
            _settings_cache.clear()
            _file_cache.clear()
            _channel_cache.clear()
            _keyboard_cache.clear()
            get_user_cached_lru.cache_clear()
            get_setting.cache_clear()
            get_main_keyboard_fast.cache_clear()
            get_data_cached.cache_clear()
        
        await m.reply("**• پاکسازی تمامی کش ها انجام شد.**")
    
    elif command == "stats":
        with _cache_lock:
            user_cache_size = len(_user_cache)
            settings_cache_size = len(_settings_cache)
            file_cache_size = len(_file_cache)
            channel_cache_size = len(_channel_cache)
            keyboard_cache_size = len(_keyboard_cache)
        
        stats_message = f"""
**آمار کش‌ها:**

• کاربران: {user_cache_size}
• تنظیمات: {settings_cache_size}
• فایل‌ها: {file_cache_size}
• کانال: {channel_cache_size}
• کیبوردها: {keyboard_cache_size}

• LRU User Cache: {get_user_cached_lru.cache_info()}
• LRU Settings Cache: {get_setting.cache_info()}
        """
        await m.reply(stats_message)
    
    elif command == "optimize":
        _clean_expired_cache()
        await m.reply("**• بهینه سازی کش های قدیمی انجام شد.**")

@app.on_message(filters.private & filters.command("testdb"))
async def test_database(c, m):
    
    await app.send_message(m.chat.id, "**شروع تست . . .**")
    
    try:
        connection = pymysql.connect(
            host="localhost",
            user=DBUser,
            password=DBPass,
            database=DBName,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        await app.edit_message_text(m.chat.id, m_id, "**• اتصال انجام شد ✅**")
        
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE 'user'")
            tables = cursor.fetchone()
            
            if tables:
                await app.edit_message_text(m.chat.id, m_id, "**• اطلاعات وجود دارد ✅**")
            else:
                await app.edit_message_text(m.chat.id, m_id, "**• جداول وجود ندارند!**")
                connection.close()
                return
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM user")
            result = cursor.fetchone()
            count = result['count'] if result else 0
            await app.edit_message_text(m.chat.id, m_id, f"**• تعداد کاربران [ {count} ]**")
        
        test_id = m.chat.id
        
        with connection.cursor() as cursor:
            cursor.execute(f"""
                INSERT INTO user (id, step, expir) 
                VALUES ({test_id}, 'test_step', 99)
                ON DUPLICATE KEY UPDATE step = 'test_step', expir = 99
            """)
            connection.commit()
            await app.edit_message_text(m.chat.id, m_id, "**• تست INSERT شد.**")
        
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT id, step, expir FROM user WHERE id = {test_id}")
            result = cursor.fetchone()
            
            if result:
                message = f"""**
✅ SELECT موفق:

آیدی: `{result['id']}`
Step: `{result.get('step', 'none')}`
Expir: `{result.get('expir', 0)}`
                **"""
                await app.edit_message_text(m.chat.id, m_id, message)
            else:
                await app.edit_message_text(m.chat.id, m_id, "**• عملیات [ SELECT ] شکست خورد.**")
        
        with connection.cursor() as cursor:
            cursor.execute(f"UPDATE user SET step = 'none' WHERE id = {test_id}")
            connection.commit()
            await app.edit_message_text(m.chat.id, m_id, "**• عملیات [ UPDATE ] انجام شد.**")
        
        connection.close()
        await app.send_message(m.chat.id, "**• تمامی تست های دیتابیس ربات انجام شد، دیتابیس نصب و متصل است.**")
        
    except pymysql.err.OperationalError as e:
        await app.send_message(m.chat.id, f"**• خطای اتصال : {str(e)[:100]}**")
    except Exception as e:
        await app.send_message(m.chat.id, f"**• خطای اتصال : {type(e).__name__}: {str(e)[:100]}**")

@app.on_message(filters.private)
@checker
async def message_handler(c, m):
    global temp_Client
    user = get_user_info(m.chat.id)
    username = f"@{m.from_user.username}" if m.from_user.username else "وجود ندارد"
    expir = user["expir"] if user else 0
    chat_id = m.chat.id
    text = m.text
    m_id = m.id
    query = f"SELECT step FROM user WHERE id = {chat_id}"
    result = get_data(query)
    
    if not user:
        update_data(f"INSERT INTO user(id) VALUES('{m.chat.id}')")
        user = {"id": m.chat.id, "step": "none", "phone": None, "expir": 0}
        invalidate_user_cache(m.chat.id)
    
    if user.get("step") == "card_photo":
        if m.photo:
            photo_path = await m.download(file_name=f"cards/{chat_id}_{int(time.time())}.jpg")
            update_data(f"UPDATE user SET step = 'card_number-{photo_path}-{m_id}' WHERE id = '{m.chat.id}' LIMIT 1")
            
            await app.send_message(chat_id,
                                 "**• لطفا شماره کارت خود را به صورت اعداد انگلیسی ارسال کنید.\nدر صورتی که منصرف شدید ربات را مجدد [ /start ] کنید.**")
        else:
            await app.send_message(chat_id, "**• فقط ارسال عکس مجاز است.**")

    elif user.get("step").startswith("card_number-"):
        if text and text.isdigit() and len(text) == 16:
            parts = user["step"].split("-", 2)
            photo_path = parts[1]
            photo_message_id = parts[2] if len(parts) > 2 else None
        
            card_number = text.strip()
    
            add_card(chat_id, card_number)
    
            if photo_message_id:
                try:
                    forwarded_photo_msg = await app.forward_messages(
                        from_chat_id=chat_id,
                        chat_id=Admin,
                        message_ids=int(photo_message_id)
                    )
                
                    await app.send_message(
                        Admin,
                        f"""**• درخواست احراز هویت از طرف ( {html.escape(m.chat.first_name)} - @{m.from_user.username if m.from_user.username else 'ندارد'} - {m.chat.id} )
شماره کارت : [ {card_number} ]**""",
                        reply_to_message_id=forwarded_photo_msg.id,
                        reply_markup=InlineKeyboardMarkup([
                            [
                                InlineKeyboardButton(text="تایید (✅)", callback_data=f"AdminVerifyCard-{chat_id}-{card_number}")
                            ],
                            [
                                InlineKeyboardButton(text="اشتباه (❌)", callback_data=f"AdminRejectCard-{chat_id}-{card_number}"),
                                InlineKeyboardButton(text="کامل نیست (❌)", callback_data=f"AdminIncompleteCard-{chat_id}-{card_number}")
                            ]
                        ])
                    )
                except Exception as e:
                    await app.send_message(
                        Admin,
                        f"""**• درخواست احراز هویت از طرف ({html.escape(m.chat.first_name)} - @{m.from_user.username if m.from_user.username else 'ندارد'} - {m.chat.id})
شماره کارت : [ {card_number} ]**""",
                        reply_markup=InlineKeyboardMarkup([
                            [
                                InlineKeyboardButton(text="تایید (✅)", callback_data=f"AdminVerifyCard-{chat_id}-{card_number}"),
                                InlineKeyboardButton(text="اشتباه (❌)", callback_data=f"AdminRejectCard-{chat_id}-{card_number}"),
                                InlineKeyboardButton(text="کامل نیست (❌)", callback_data=f"AdminIncompleteCard-{chat_id}-{card_number}")
                            ]
                        ])
                    )
            else:
                await app.send_message(
                    Admin,
                    f"""**• درخواست احراز هویت از طرف ({html.escape(m.chat.first_name)} - @{m.from_user.username if m.from_user.username else 'ندارد'} - {m.chat.id})
شماره کارت : [ {card_number} ]**""",
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton(text="تایید (✅)", callback_data=f"AdminVerifyCard-{chat_id}-{card_number}"),
                            InlineKeyboardButton(text="اشتباه (❌)", callback_data=f"AdminRejectCard-{chat_id}-{card_number}"),
                            InlineKeyboardButton(text="کامل نیست (❌)", callback_data=f"AdminIncompleteCard-{chat_id}-{card_number}")
                        ]
                    ])
                )
    
            await app.send_message(chat_id,
                            """**• درخواست احراز هویت شما برای پشتیبانی ارسال شد و در اولین فرصت تایید خواهد شد ، لطفا صبور باشید.

لطفا برای تایید کارت به پشتیبانی پیام ارسال نفرمایید و درخواست احرازهویتتون رو اسپم نکنید ، در صورت مشاهده این کار یک روز با تاخیر تایید میشود.**""")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
        else:
            await app.send_message(chat_id, "**شماره کارت باید 16 رقم باشد.\n• در صورتی که منصرف شدید ربات رو مجددا [ /start ] کنید.**")

    elif user.get("step").startswith("payment_receipt-"):
        if m.photo:
            params = user["step"].split("-")
            expir_count = params[1]
            cost = params[2]
            card_id = params[3]
            
            card = get_card_by_id(card_id)
            card_number = card["card_number"] if card else "نامشخص"
            
            mess = await app.forward_messages(from_chat_id=chat_id, chat_id=Admin, message_ids=m_id)
            
            transaction_id = str(int(time.time()))[-11:]
            
            await app.send_message(Admin,
                                 f"""**• درخواست خرید اشتراک از طرف ( {html.escape(m.chat.first_name)} - @{m.from_user.username if m.from_user.username else 'ندارد'} - {m.chat.id} )
اشتراک انتخاب شده : ( `{cost} تومان - {expir_count} روز` )
کارت خرید : ( `{card_number}` )**""",
                                 reply_to_message_id=mess.id,
                                 reply_markup=InlineKeyboardMarkup([
                                     [InlineKeyboardButton(text="تایید (✅)", callback_data=f"AdminApprovePayment-{chat_id}-{expir_count}-{cost}-{transaction_id}")],
                                      [InlineKeyboardButton(text="مسدود (❌)", callback_data=f"AdminBlockPayment-{chat_id}"),
                                      InlineKeyboardButton(text="رد (❌)", callback_data=f"AdminRejectPayment-{chat_id}-{transaction_id}")]
                                 ]))
            
            await app.send_message(chat_id,
                                 f"""**فیش واریزی شما ارسال شد.
• شناسه تراکنش: [ `{transaction_id}` ]
منتظر تایید فیش توسط مدیر باشید.**""")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
        else:
            await app.send_message(chat_id, "**فقط عکس فیش واریزی را ارسال کنید.**")

    elif user.get("step") == "support":
        mess = await app.forward_messages(from_chat_id=chat_id, chat_id=Admin, message_ids=m_id)
        await app.send_message(Admin, f"""**
• پیام جدید از طرف ( {html.escape(m.chat.first_name)} - `{m.chat.id}` - {username} )**\n
""", reply_to_message_id=mess.id, reply_markup=InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("پاسخ (✅)", callback_data=f"Reply-{m.chat.id}"),
                InlineKeyboardButton("مسدود (❌)", callback_data=f"Block-{m.chat.id}")
            ]
        ]
    ))
        await app.send_message(chat_id, "**• پیام شما به پشتیبانی ارسال شد.\nلطفا در بخش پشتیبانی اسپم نکنید و از دستورات استفاده نکنید به پیام شما در اسرع وقت پاسخ داده خواهد شد.**", reply_to_message_id=m_id)
    
    elif user.get("step").startswith("awaiting_code_confirmation-"):
        if text and text.strip():
            code = text.strip()
            
            await confirm_auto_api_code(chat_id, m_id, code, False)
        else:
            await app.send_message(chat_id, "**لطفا کد تأیید را وارد کنید.**")
    
    elif user.get("step") == "EnterNewCode":
        if text and text.strip():
            code = text.strip()
            
            await confirm_auto_api_code(chat_id, m_id, code, False)
        else:
            await app.send_message(chat_id, "**لطفا کد تأیید جدید را وارد کنید.**")
    
    elif user.get("step") == "edit_merchant_id":
        if chat_id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{chat_id}' LIMIT 1") is not None:
            merchant_id = text.strip()
        
            if len(merchant_id) == 36 and '-' in merchant_id:
                current_status = get_gateway_status()
                success = update_gateway_settings(
                    "zarinpal", 
                    merchant_id, 
                    current_status.get("sandbox", True), 
                    current_status.get("active", False)
                )
            
                if success:
                    await app.send_message(
                        chat_id,
                        f"**• مرچنت کد ( `{merchant_id}` ) تنظیم شد.**",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("(🔙) بازگشت", callback_data="GatewaySettings")]
                        ])
                    )
                else:
                    await app.send_message(
                        chat_id,
                        "**خطا در بروزرسانی!**",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("(🔙) بازگشت", callback_data="GatewaySettings")]
                        ])
                    )
            else:
                await app.send_message(
                    chat_id,
                    "**فرمت ارسالی صحیح نیست.**",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("(🔙) بازگشت", callback_data="GatewaySettings")]
                    ])
                )
        
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
    
    elif user.get("step") == "install_phone":
        if m.contact:
            phone_number = str(m.contact.phone_number)
            if not phone_number.startswith("+"):
                phone_number = f"+{phone_number}"
            
            update_data(f"UPDATE user SET phone = '{phone_number}' WHERE id = '{chat_id}'")
            
            await app.send_message(
                chat_id,
                f"**» لطفا انتخاب کنید:\n**"
                f"**میخواهید به صورت دستی Api Id , Hash را وارد کنید یا ربات به صورت خودکار این کار را انجام دهد؟\n\n**",
                "‌‌‌‌ ‌           ‌‌‌‌ ",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("دستی 👤", callback_data="ManualInstall"),
                    InlineKeyboardButton("خودکار 🤖", callback_data="AutoInstall")],
                    [InlineKeyboardButton("(🔙) بازگشت", callback_data="Back")]
                ])
            )
            
            update_data(f"UPDATE user SET step = 'select_install_method' WHERE id = '{chat_id}'")
        else:
            await app.send_message(chat_id, "**لطفا با استفاده از دکمه، شماره تلفن را به اشتراک بگذارید.**")

    elif user.get("step") == "install_api_id":
        if text and text.isdigit():
            update_data(f"UPDATE user SET api_id = '{text}' WHERE id = '{chat_id}'")
            update_data(f"UPDATE user SET step = 'install_api_hash' WHERE id = '{chat_id}'")
            await app.send_message(m.chat.id, f"**• لطفا `Api Hash` خود را وارد کنید.\n( مثال : abcdefg0123456abcdefg123456789c )\n\n• لغو عملیات [ /start ]**")
        else:
            await app.send_message(chat_id, "**• لطفا یک Api ID معتبر وارد کنید.**")

    elif user.get("step") == "install_api_hash":
        if text and len(text) == 32:
            update_data(f"UPDATE user SET api_hash = '{text}' WHERE id = '{chat_id}'")
        
            user_info = get_data(f"SELECT phone, api_id, api_hash FROM user WHERE id = '{chat_id}' LIMIT 1")
            
            api_hash = user_info["api_hash"]
            if len(api_hash) >= 8:
                masked_hash = f"{api_hash[:4]}{'*' * (len(api_hash)-8)}{api_hash[-4:]}"
            else:
                masked_hash = "****"
            
            await app.send_message(chat_id,
                f"**📞 Number : `{user_info['phone']}`\n🆔 Api ID : `{user_info['api_id']}`\n🆔 Api Hash : `{masked_hash}`\n\n• آیا اطلاعات را تایید میکنید؟          ‌‌‌‌          **",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("بله (✅)", callback_data="ConfirmInstall"),
                    InlineKeyboardButton("خیر (❎)", callback_data="ChangeInfo")],
                    [InlineKeyboardButton("(🔙) بازگشت", callback_data="Back")]
            ]))
            
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}'")
        else:
            await app.send_message(chat_id, "**لطفا یک Api Hash معتبر وارد کنید.**")

    elif user.get("step").startswith("install_with_language-"):
        parts = user["step"].split("-")
        if len(parts) >= 5:
            phone = parts[1]
            api_id = parts[2]
            api_hash = parts[3]
            language = parts[4]
        
            if text:
                if "." in text:
                    code = "".join(text.split("."))
                else:
                    code = text
        
                if code.isdigit() and len(code) == 5:
                    await verify_code_and_login(chat_id, phone, api_id, api_hash, code, language)
                else:
                    await app.send_message(chat_id, "**• کد وارد شده نامعتبر است، مجدد کد را وارد کنید.**")
            else:
                await app.send_message(chat_id, "**لطفا کد تأیید را ارسال کنید.**")

    elif user.get("step").startswith("install_code-"):
        parts = user["step"].split("-")
        phone = parts[1]
        api_id = parts[2]
        api_hash = parts[3]
        language = parts[4] if len(parts) > 4 else "fa"

        if text:
            if "." in text:
                code = "".join(text.split("."))
            else:
                code = text
    
            if code.isdigit() and len(code) == 5:
                await verify_code_and_login(chat_id, phone, api_id, api_hash, code, language)
        
        else:
            await app.send_message(chat_id, "**لطفا کد تأیید را ارسال کنید.**")

    elif user.get("step").startswith("install_2fa-"):
        parts = user["step"].split("-")
        phone = parts[1]
        api_id = parts[2]
        api_hash = parts[3]
        language = parts[4] if len(parts) > 4 else "fa"

        if text:
            await verify_2fa_password(chat_id, phone, api_id, api_hash, text, language)
        else:
            await app.send_message(chat_id, "**• لطفا رمز دومرحله ای اکانت را بدون هیچ کلمه یا کاراکتر اضافه ای ارسال کنید :**")
    
    elif user.get("step") == "admin_create_code_days":
        if chat_id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{chat_id}' LIMIT 1") is not None:
            if text.isdigit():
                days = int(text.strip())
                code = create_code(days)
                await app.send_message(chat_id,
                                 f"**• کد انقضا با موفقیت ایجاد شد.\n**"
                                 f"**• کد : ( `{code}` )**\n"
                                 f"**• تعداد روز : ( {days} روز )**\n\n"
                                 f"**• تاریخ ثبت : ( `{time.strftime('%Y-%m-%d %H:%M:%S')}` )",
                                 reply_markup=InlineKeyboardMarkup([
                                     [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]
                                 ]))
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
            else:
                await app.send_message(chat_id, "**لطفا یک عدد معتبر وارد کنید.**")

    elif user.get("step") == "use_code":
        code_value = text.strip().upper()
        code_data = get_code_by_value(code_value)
        
        if code_data:
            user_data = get_data(f"SELECT expir FROM user WHERE id = '{chat_id}' LIMIT 1")
            old_expir = user_data["expir"] if user_data else 0
            new_expir = old_expir + code_data["days"]
            
            update_data(f"UPDATE user SET expir = '{new_expir}' WHERE id = '{chat_id}' LIMIT 1")
            
            use_code(code_value, chat_id)
            
            user_info = await app.get_users(chat_id)
            username = f"@{user_info.username}" if user_info.username else "ندارد"
            
            days = code_data["days"]
            if days == 31:
                month_text = "یک ماه"
            elif days == 62:
                month_text = "دو ماه"
            elif days == 93:
                month_text = "سه ماه"
            elif days == 124:
                month_text = "چهار ماه"
            elif days == 155:
                month_text = "پنج ماه"
            elif days == 186:
                month_text = "شش ماه"
            else:
                month_text = f"{days} روز"
            
            message_to_user = f"**• افزایش انقضا با موفقیت انجام شد.\n**"
            message_to_user += f"**• کد شارژ استفاده شده : ( `{code_value}` )**\n"
            message_to_user += f"**• انقضای سلف شما {month_text} اضافه گردید.**\n\n"
            message_to_user += f"**• انقضای قبلی شما : ( `{old_expir}` روز )**\n\n"
            message_to_user += f"**• انقضای جدید : ( `{new_expir}` روز )**"
            
            await app.send_message(chat_id, message_to_user)
            
            message_to_admin = f"**کاربر ( {html.escape(user_info.first_name)} - {username} - {chat_id} ) با استفاده از کد ( `{code_value}` ) مقدار {month_text} انقضا خریداری کرد و این کد از لیست کدها حذف شد.**"
            await app.send_message(Admin, message_to_admin)
            
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
        else:
            await app.send_message(chat_id, "**کد ارسالی صحیح نیست.**")
            
    elif user.get("step") == "edit_start_message":
        if chat_id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{chat_id}' LIMIT 1") is not None:
            update_setting("start_message", text)
            await app.send_message(chat_id, "**• متن شروع ربات تغییر کرد.**",
                             reply_markup=InlineKeyboardMarkup([
                                 [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminSettings")]
                             ]))
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

    elif user.get("step") == "edit_price_message":
        if chat_id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{chat_id}' LIMIT 1") is not None:
            update_setting("price_message", text)
            await app.send_message(chat_id, "**• متن نرخ اشتراک تغییر کرد.**",
                             reply_markup=InlineKeyboardMarkup([
                                 [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminSettings")]
                             ]))
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

    elif user.get("step") == "edit_self_message":
        if chat_id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{chat_id}' LIMIT 1") is not None:
            update_setting("whatself_message", text)
            await app.send_message(chat_id, "**• متن توضیح ربات سلف تغییر کرد.**",
                             reply_markup=InlineKeyboardMarkup([
                                 [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminSettings")]
                             ]))
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

    elif user.get("step") == "edit_all_prices":
        if chat_id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{chat_id}' LIMIT 1") is not None:
            lines = text.strip().split('\n')
        
            if len(lines) != 6:
                await app.send_message(chat_id, "**خطا: باید دقیقا 6 قیمت (هر قیمت در یک خط) وارد کنید.**\n\n**فرمت صحیح:**\n```\nقیمت 1 ماهه\nقیمت 2 ماهه\nقیمت 3 ماهه\nقیمت 4 ماهه\nقیمت 5 ماهه\nقیمت 6 ماهه\n```",
                                reply_markup=InlineKeyboardMarkup([
                                    [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminSettings")]
                                ]))
                return
        
            price_keys = ['1month', '2month', '3month', '4month', '5month', '6month']
            price_names = {
                '1month': '1 ماهه',
                '2month': '2 ماهه', 
                '3month': '3 ماهه',
                '4month': '4 ماهه',
                '5month': '5 ماهه',
                '6month': '6 ماهه'
            }
        
            valid_prices = []
            errors = []
        
            for i, line in enumerate(lines):
                price_text = line.strip()
                if not price_text.isdigit():
                    errors.append(f"**نرخ {price_names[price_keys[i]]} باید عدد باشد : {price_text}**")
                else:
                    valid_prices.append((price_keys[i], price_text))
        
            if errors:
                error_text = "**خطا در ورود نرخ**\n\n"
                for error in errors:
                    error_text += f"• {error}\n"
                error_text += "\n**لطفا مجددا تلاش کنید.**"
            
                await app.send_message(chat_id, error_text,
                                 reply_markup=InlineKeyboardMarkup([
                                     [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminSettings")]
                                ]))
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
                return
        
            success_text = "**• نرخ شما تعیین شد.**\n\n"
            for key, price in valid_prices:
                update_setting(f"price_{key}", price)
        
            await app.send_message(chat_id, success_text,
                            reply_markup=InlineKeyboardMarkup([
                                 [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminSettings")]
                            ]))
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

    elif user.get("step") == "edit_card_number":
        if chat_id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{chat_id}' LIMIT 1") is not None:
            if text.replace(" ", "").isdigit() and len(text.replace(" ", "")) >= 16:
                update_setting("card_number", text.replace(" ", ""))
                await app.send_message(chat_id, f"**• شماره کارت با موفقیت به ( `{text}` ) تغییر کرد.**",
                                 reply_markup=InlineKeyboardMarkup([
                                     [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminSettings")]
                                 ]))
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
            else:
                await app.send_message(chat_id, "**شماره کارت نامعتبر است. لطفا یک شماره کارت معتبر وارد کنید.**")

    elif user.get("step") == "edit_card_name":
        if chat_id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{chat_id}' LIMIT 1") is not None:
            update_setting("card_name", text)
            await app.send_message(chat_id, f"**• نام مالک کارت به ( `{text}` ) تغییر کرد.**",
                             reply_markup=InlineKeyboardMarkup([
                                 [InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminSettings")]
                             ]))
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
    
    elif user.get("step") == "admin_broadcast":
        if chat_id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{chat_id}' LIMIT 1") is not None:
            mess = await app.send_message(chat_id, "**• ارسال پیام شما درحال انجام است، لطفا صبور باشید.**")
            users = get_datas(f"SELECT id FROM user")
            for user in users:
                await app.copy_message(from_chat_id=chat_id, chat_id=user[0], message_id=m_id)
                await asyncio.sleep(0.1)
            await app.edit_message_text(chat_id, mess.id, "**• پیام شما به تمامی کاربران ارسال شد.**", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
            ))
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
    
    elif user.get("step") == "admin_forward":
        if chat_id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{chat_id}' LIMIT 1") is not None:
            mess = await app.send_message(chat_id, "**• فوروارد پیام شما درحال انجام است، لطفا صبور باشید.**")
            users = get_datas(f"SELECT id FROM user")
            for user in users:
                await app.forward_messages(from_chat_id=chat_id, chat_id=user[0], message_ids=m_id)
                await asyncio.sleep(0.1)
            await app.edit_message_text(chat_id, mess.id, "**• پیام شما به تمامی کاربران فوروارد شد.**", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
            ))
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
    
    elif user.get("step") == "admin_block":
        if chat_id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{chat_id}' LIMIT 1") is not None:
            if text.isdigit():
                user_id = int(text.strip())
                if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                    block = get_data(f"SELECT * FROM block WHERE id = '{user_id}' LIMIT 1")
                    if block is None:
                        await app.send_message(user_id, f"**شما به دلیل نقض قوانین از ربات مسدود شدید.\n• با پشتیان ها در ارتباط باشید.**")
                        await app.send_message(chat_id, f"**کاربر [ `{user_id}` ] از ربات مسدود شد.**", reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                        ))
                        update_data(f"INSERT INTO block(id) VALUES({user_id})")
                    else:
                        await app.send_message(chat_id, f"**کاربر [ `{user_id}` ] از ربات مسدود شد.**", reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                        ))
                else:
                    await app.send_message(chat_id, "**کاربر پیدا نشد.\n• ابتدا آیدی کاربر را بررسی کرده و از ربات بخواهید ربات را [ /start ] کند.**", reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                    ))
            else:
                await app.send_message(chat_id, "**فقط ارسال عدد مجاز است.**", reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                ))
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
    
    elif user.get("step") == "admin_unblock":
        if chat_id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{chat_id}' LIMIT 1") is not None:
            if text.isdigit():
                user_id = int(text.strip())
                if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                    block = get_data(f"SELECT * FROM block WHERE id = '{user_id}' LIMIT 1")
                    if block is not None:
                        await app.send_message(user_id, f"**شما توسط مدیر از لیست سیاه ربات خارج شدید.\n• اکنون میتوانید از ربات استفاده کنید.**")
                        await app.send_message(chat_id, f"**کاربر [ `{user_id}` ] از لیست سیاه خارج شد.**", reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                        ))
                        update_data(f"DELETE FROM block WHERE id = '{user_id}' LIMIT 1")
                    else:
                        await app.send_message(chat_id, f"**کاربر [ `{user_id}` ] در لیست سیاه وجود ندارد.**", reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                        ))
                else:
                    await app.send_message(chat_id, "**کاربر پیدا نشد.\n•ابتدا آیدی ربات را بررسی کرده و از کاربر بخواهید ربات را [ /start ] کند.**", reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                    ))
            else:
                await app.send_message(chat_id, "**فقط ارسال عدد مجاز است.**", reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                ))
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
    
    elif user.get("step") == "admin_add_expiry1":
        if chat_id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{chat_id}' LIMIT 1") is not None:
            if text.isdigit():
                user_id = int(text.strip())
                if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                    await app.send_message(chat_id, "**• آیدی عددی کاربر را جهت افزایش انقضا ارسال کنید.**", reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                    ))
                    update_data(f"UPDATE user SET step = 'admin_add_expiry2-{user_id}' WHERE id = '{chat_id}' LIMIT 1")
                else:
                    await app.send_message(chat_id, f"**کاربر پیدا نشد.\n• ابتدا آیدی کاربر را بررسی کرده و از کاربر بخواهید ربات را [ /start ] کند.**", reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                    ))
            else:
                await app.send_message(chat_id, "**فقط ارسال عدد مجاز است.**", reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                ))
    
    elif user.get("step").startswith("admin_add_expiry2"):
        if chat_id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{chat_id}' LIMIT 1") is not None:
            if text.isdigit():
                user_id = int(user["step"].split("-")[1])
                count = int(text.strip())
                user_expir = get_data(f"SELECT expir FROM user WHERE id = '{user_id}' LIMIT 1")
                user_upexpir = int(user_expir["expir"]) + int(count)
                update_data(f"UPDATE user SET expir = '{user_upexpir}' WHERE id = '{user_id}' LIMIT 1")
                
                await app.send_message(user_id, f"**افزایش انقضا برای شما انجام شد.\n• ( `{count}` روز ) به انقضای شما اضافه گردید.\n\n• انقضای جدید شما : ( {user_upexpir} روز )\n")
                
                await app.send_message(chat_id, f"**افزایش انقضا برای کاربر [ `{user_id}` ] انجام شد.\n\n• انقضای اضافه شده: ( `{count}` روز )\n• انقضای جدید کاربر : ( `{user_upexpir}` روز )**", reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                ))
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
            else:
                await app.send_message(chat_id, "**فقط ارسال عدد مجاز است.**", reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                ))
    
    elif user.get("step") == "admin_deduct_expiry1":
        if chat_id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{chat_id}' LIMIT 1") is not None:
            if text.isdigit():
                user_id = int(text.strip())
                if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                    await app.send_message(chat_id, "**زمان انقضای موردنظر را برای کاهش ارسال کنید:**", reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                    ))
                    update_data(f"UPDATE user SET step = 'admin_deduct_expiry2-{user_id}' WHERE id = '{chat_id}' LIMIT 1")
                else:
                    await app.send_message(chat_id, f"**کاربر پیدا نشد.\n• ابتدا آیدی کاربر را بررسی کرده و از کاربر بخواهید ربات را [ /start ] کند.**", reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                    ))
            else:
                await app.send_message(chat_id, "**فقط ارسال عدد مجاز است.**", reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                ))
    
    elif user.get("step").startswith("admin_deduct_expiry2"):
        if chat_id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{chat_id}' LIMIT 1") is not None:
            if text.isdigit():
                user_id = int(user["step"].split("-")[1])
                count = int(text.strip())
                user_expir = get_data(f"SELECT expir FROM user WHERE id = '{user_id}' LIMIT 1")
                user_upexpir = int(user_expir["expir"]) - int(count)
                update_data(f"UPDATE user SET expir = '{user_upexpir}' WHERE id = '{user_id}' LIMIT 1")
                
                await app.send_message(user_id, f"**کسر انقضا برای شما انجام شد.\n\nانقضای جدید شما : ( `{user_upexpir}` روز )\n\n• انقضای کسر شده ؛ ( `{count}` روز )**")
                
                await app.send_message(chat_id, f"**کسر انقضا برای کاربر [ `{user_id}` ] انجام شد.\n\n• انقضای کسر شده: ( `{count}` روز )\n• انقضای جدید کاربر : ( `{user_upexpir}` روز )**", reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                ))
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
            else:
                await app.send_message(chat_id, "**فقط ارسال عدد مجاز است.**", reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                ))
    
    elif user.get("step") == "admin_activate_self":
        if chat_id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{chat_id}' LIMIT 1") is not None:
            if text.isdigit():
                user_id = int(text.strip())
                if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                    if os.path.isfile(f"sessions/{user_id}.session-journal"):
                        user_data = get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1")
                        if user_data["self"] != "active":
                            mess = await app.send_message(chat_id, f"**• اشتراک سلف برای کاربر [ `{user_id}` ] درحال فعالسازی است، لطفا صبور باشید.**")
                            process = subprocess.Popen(["python3", "self.py", str(user_id), str(API_ID), API_HASH, Helper_ID], cwd=f"selfs/self-{user_id}")
                            await asyncio.sleep(10)
                            if process.poll() is None:
                                await app.edit_message_text(chat_id, mess.id, f"**• ربات سلف با موفقیت برای کاربر [ `{user_id}` ] فعال شد.**", reply_markup=InlineKeyboardMarkup(
                                    [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                                ))
                                update_data(f"UPDATE user SET self = 'active' WHERE id = '{user_id}' LIMIT 1")
                                update_data(f"UPDATE user SET pid = '{process.pid}' WHERE id = '{user_id}' LIMIT 1")
                                add_admin(user_id)
                                await setscheduler(user_id)
                                await app.send_message(user_id, f"**• اشتراک سلف توسط مدیریت برای شما فعال شد.\nاکنون مجاز به استفاده از ربات دستیار میباشید.**")
                            else:
                                await app.edit_message_text(chat_id, mess.id, f"**فعالسازی سلف برای کاربر [ `{user_id}` ] با خطا مواجه شد.**", reply_markup=InlineKeyboardMarkup(
                                    [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                                ))
                        else:
                            await app.send_message(chat_id, f"**اشتراک سلف برای کاربر [ `{user_id}` ] غیرفعال بوده است.**", reply_markup=InlineKeyboardMarkup(
                                [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                            ))
                    else:
                        await app.send_message(chat_id, f"**کاربر [ `{user_id}` ] اشتراک فعالی ندارد.**", reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                        ))
                else:
                    await app.send_message(chat_id, "**کاربر یافت نشد، ابتدا از کاربر بخواهید ربات را [ /start ] کند.**", reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                    ))
            else:
                await app.send_message(chat_id, "**فقط ارسال عدد مجاز است.**", reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                ))
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
    
    elif user.get("step") == "admin_deactivate_self":
        if chat_id == Admin or helper_getdata(f"SELECT * FROM adminlist WHERE id = '{chat_id}' LIMIT 1") is not None:
            if text.isdigit():
                user_id = int(text.strip())
                if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                    if os.path.isfile(f"sessions/{user_id}.session-journal"):
                        user_data = get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1")
                        if user_data["self"] != "inactive":
                            mess = await app.send_message(chat_id, "**• درحال پردازش، لطفا صبور باشید.**")
                            try:
                                os.kill(user_data["pid"], signal.SIGKILL)
                            except:
                                pass
                            await app.edit_message_text(chat_id, mess.id, f"**• ربات سلف برای کاربر [ `{user_id}` ] غیرفعال شد.**", reply_markup=InlineKeyboardMarkup(
                                [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                            ))
                            update_data(f"UPDATE user SET self = 'inactive' WHERE id = '{user_id}' LIMIT 1")
                            if user_id != Admin:
                                delete_admin(user_id)
                            job = scheduler.get_job(str(user_id))
                            if job:
                                scheduler.remove_job(str(user_id))
                            await app.send_message(user_id, f"**کاربر [ `{user_id}` ] سلف شما به دلایلی غیرفعال شد، لطفا با پشتیبان ها در ارتباط باشید.**")
                        else:
                            await app.send_message(chat_id, f"**ربات سلف از قبل برای کاربر [ `{user_id}` ] غیرفعال بوده است.**", reply_markup=InlineKeyboardMarkup(
                                [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                            ))
                    else:
                        await app.send_message(chat_id, f"**کاربر [ `{user_id}` ] انقضای فعالی ندارد.**", reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                        ))
                else:
                    await app.send_message(chat_id, "**کاربر یافت نشد، ابتدا از کاربر بخواهید ربات را [ /start ] کند.**", reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                    ))
            else:
                await app.send_message(chat_id, "**فقط ارسال عدد مجاز است.**", reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
                ))
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
            
    elif user.get("step").startswith("ureply-"):
        user_id = int(user["step"].split("-")[1])
        mess = await app.copy_message(from_chat_id=Admin, chat_id=user_id, message_id=m_id)
        await app.send_message(user_id, "**• کاربر گرامی، پاسخ شما از پشتیبانی دریافت شد.**", reply_to_message_id=mess.id)
        await app.send_message(Admin, "**• پیام شما برای کاربر ارسال شد.**", reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="(🔙) بازگشت", callback_data="AdminPanel")]]
        ))
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{Admin}' LIMIT 1")

def initialize_settings():
    default_settings = [
        ("start_message", "**سلام {user_link}، به ربات خرید دستیار تلگرام خوش آمدید!**", "پیام استارت"),
        ("price_message", "**نرخ‌ها:**\n1 ماهه: {price_1month} تومان\n2 ماهه: {price_2month} تومان", "پیام نرخ"),
        ("whatself_message", "**سلف رباتی است که روی اکانت شما نصب می‌شود...**", "پیام توضیح سلف"),
        ("price_1month", "75000", "قیمت 1 ماهه"),
        ("price_2month", "150000", "قیمت 2 ماهه"),
        ("price_3month", "220000", "قیمت 3 ماهه"),
        ("price_4month", "275000", "قیمت 4 ماهه"),
        ("price_5month", "340000", "قیمت 5 ماهه"),
        ("price_6month", "390000", "قیمت 6 ماهه"),
        ("card_number", CardNumber, "شماره کارت"),
        ("card_name", CardName, "نام صاحب کارت"),
        ("phone_restriction", "enabled", "محدودیت شماره")
    ]
    
    for key, value, description in default_settings:
        existing = get_data(f"SELECT * FROM settings WHERE setting_key = '{key}'")
        if not existing:
            update_data(f"INSERT INTO settings (setting_key, setting_value, description) VALUES ('{key}', '{value}', '{description}')")
            print(f"✓ Added default setting: {key}")

async def optimize_database():
    try:
        update_data("""
            DELETE FROM codes 
            WHERE is_active = FALSE 
            AND created_at < DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        tables = ['user', 'cards', 'codes', 'settings', 'payment_transactions']
        for table in tables:
            try:
                update_data(f"OPTIMIZE TABLE {table}")
            except:
                pass
        
        print("✅ Database optimized")
    except Exception as e:
        print(f"Database optimization error: {e}")

#==================== Fast Startup =====================#
async def warm_up_caches():
    print("🔥 Loading Main Settings . . .")
    
    important_settings = [
        'start_message', 'price_message', 'whatself_message',
        'price_1month', 'price_2month', 'price_3month',
        'price_4month', 'price_5month', 'price_6month',
        'card_number', 'card_name', 'phone_restriction'
    ]
    
    for setting in important_settings:
        get_setting(setting)
    get_user_cached_lru(Admin)
    print("Main Settings Initialize compileted!")

#================== Run ===================#

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(optimize_database, "cron", hour=3, minute=0, id="db_optimization")
    scheduler.start()
    
    await warm_up_caches()
    initialize_settings()
    _clean_expired_cache()
    
    await app.start()
    
    bot = await app.get_me()
    print(Fore.YELLOW + "Ultra Self Bot v2.0.0 Started...")
    print(Fore.GREEN + f"Bot is running as: @{bot.username}")
    print(Fore.CYAN + "Press Ctrl+C to stop the bot")
    await idle()
    await app.stop()
    scheduler.shutdown()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print(Fore.RED + "\nBot stopped by user")
    finally:
        if loop.is_running():
            loop.close()