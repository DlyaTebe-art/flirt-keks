#!/usr/bin/env python3
import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "bot.db")  # якщо в .env задано /app/bot.db, docker-compose прокинить це

print("Ініціалізація бази:", DB_PATH)
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Таблиця users
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    is_banned INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now','localtime'))
);
""")

# Таблиця ads (ogoloshennya / posts)
c.execute("""
CREATE TABLE IF NOT EXISTS ads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT,            -- 'public' або 'anonymous'
    name TEXT,
    age INTEGER,
    gender TEXT,
    looking_for TEXT,
    content TEXT,
    photo_file_id TEXT,
    tg_username TEXT,
    status TEXT DEFAULT 'pending',  -- pending/approved/rejected
    created_at DATETIME DEFAULT (datetime('now','localtime'))
);
""")

# Таблиця replies (vidpovidi)
c.execute("""
CREATE TABLE IF NOT EXISTS replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_id INTEGER,
    sender_user_id INTEGER,
    name TEXT,
    age INTEGER,
    gender TEXT,
    content TEXT,
    photo_file_id TEXT,
    created_at DATETIME DEFAULT (datetime('now','localtime'))
);
""")

# Таблиця chats (anonimni chati)
c.execute("""
CREATE TABLE IF NOT EXISTS chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_id INTEGER,
    user_author_id INTEGER,
    user_responder_id INTEGER,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT (datetime('now','localtime'))
);
""")

conn.commit()
conn.close()
print("Готово — таблиці створені (якщо їх не було).")
