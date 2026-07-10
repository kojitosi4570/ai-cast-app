import os
import json
import sqlite3
import hashlib
import base64
import urllib.request
import urllib.error
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

# 📡 1. .env からAPIキーを自動読み込み
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

CAST_DATA_PATH = "cast_prompts_data.json"
IMAGE_DIR = "AIキャスト画像"
DB_PATH = "himakano.db"  # 💾 データベース

# 👑 ===================================================================
# 📝 【運営者情報・設定欄】
# =====================================================================
COMPANY_NAME = "合同会社小嶋企画"  # 販売事業者名
REPRESENTATIVE = "小嶋"  # 運営責任者名
ADDRESS = "神奈川県川崎市中原区..."  # 所在地
CONTACT_EMAIL = "kojitosi4570@gmail.com"  # 問い合わせ先メール
# =====================================================================

# 📱 スマホ専用画面に最適化
st.set_page_config(
    page_title="AIキャスト チャット", 
    page_icon="💬", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# 🎨 スマホ表示を極限まで美しくする最高峰カスタムCSS
st.markdown("""
    <style>
        [data-testid='collapsedControl'] { display: none; }
        .block-container { padding-top: 2.0rem !important; padding-bottom: 5rem !important; max-width: 450px !important; }
        .stNotification { display: none !important; } 
        
        /* 🌟 おすすめキャストをスマホでも強制的に横並び＆横スクロール化 */
        div[data-testid="element-container"]:has(#recommend-marker) + div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            overflow-x: auto !important;
            flex-wrap: nowrap !important;
            padding-bottom: 10px;
            scrollbar-width: none;
        }
        div[data-testid="element-container"]:has(#recommend-marker) + div[data-testid="stHorizontalBlock"]::-webkit-scrollbar {
            display: none;
        }
        div[data-testid="element-container"]:has(#recommend-marker) + div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            min-width: 80px !important;
            width: 80px !important;
            flex: 0 0 auto !important;
        }

        /* 🌟 いいね/スキップボタンを写真の【直下】に配置（重なりエラーを完全防止） */
        div[data-testid="element-container"]:has(#action-marker) + div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            gap: 20px !important;
            margin-top: 15px !important;
            margin-bottom: 25px !important;
        }

        /* ❌ スキップボタン（白背景 ＋ 細線の赤✕マーク） */
        div[data-testid="element-container"]:has(#action-marker) + div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-of-type(1) div.stButton > button {
            color: transparent !important;
            background-color: #ffffff !important;
            background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%23ff4d4d" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>') !important;
            background-size: 32px 32px !important;
            background-position: center !important;
            background-repeat: no-repeat !important;
            border-radius: 50% !important;
            width: 70px !important; height: 70px !important;
            min-width: 70px !important; max-width: 70px !important;
            border: 1px solid #eeeeee !important;
            box-shadow: 0px 4px 12px rgba(0,0,0,0.08) !important;
            transition: all 0.2s ease !important;
            margin: 0 auto !important;
        }
        div[data-testid="element-container"]:has(#action-marker) + div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-of-type(1) div.stButton > button:active {
            transform: scale(0.90) !important;
        }
        
        /* ❤️ いいねボタン（赤背景 ＋ 白いハート） */
        div[data-testid="element-container"]:has(#action-marker) + div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-of-type(2) div.stButton > button {
            color: transparent !important;
            background-color: #ff4d4d !important;
            background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23ffffff" stroke="none"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>') !important;
            background-size: 32px 32px !important;
            background-position: center !important;
            background-repeat: no-repeat !important;
            border-radius: 50% !important;
            width: 70px !important; height: 70px !important;
            min-width: 70px !important; max-width: 70px !important;
            border: none !important;
            box-shadow: 0px 4px 12px rgba(255,77,77,0.3) !important;
            transition: all 0.2s ease !important;
            margin: 0 auto !important;
        }
        div[data-testid="element-container"]:has(#action-marker) + div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-of-type(2) div.stButton > button:active {
            transform: scale(0.90) !important;
        }
    </style>
""", unsafe_allow_html=True)

try:
    import stripe
    if STRIPE_SECRET_KEY:
        stripe.api_key = STRIPE_SECRET_KEY
except ImportError:
    stripe = None


# =====================================================================
# 2. 🗄️ データベース（SQLite）制御エンジン
# =====================================================================
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            password_hash TEXT DEFAULT NULL,
            is_premium INTEGER DEFAULT 0,
            is_guest INTEGER DEFAULT 1
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_counts (
            user_id TEXT,
            cast_id TEXT,
            count INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, cast_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            cast_id TEXT,
            role TEXT,
            text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            user_id TEXT,
            cast_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, cast_id)
        )
    """)
    conn.commit()
    conn.close()

def make_password_hash(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def create_guest_user(guest_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (guest_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, password_hash, is_premium, is_guest) VALUES (?, NULL, 0, 1)", (guest_id,))
        conn.commit()
    conn.close()

def upgrade_guest_to_premium(guest_id, email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id FROM users WHERE user_id = ? AND is_guest = 0", (email,))
    if cursor.fetchone():
        conn.close()
        return False, "⚠️ そのメールアドレスは既にプレミアム登録されています。"
        
    password_hash = make_password_hash(password)
    
    cursor.execute("UPDATE users SET user_id = ?, password_hash = ?, is_premium = 1, is_guest = 0 WHERE user_id = ?", (email, password_hash, guest_id))
    cursor.execute("UPDATE chat_counts SET user_id = ? WHERE user_id = ?", (email, guest_id))
    cursor.execute("UPDATE chat_messages SET user_id = ? WHERE user_id = ?", (email, guest_id))
    cursor.execute("UPDATE matches SET user_id = ? WHERE user_id = ?", (email, guest_id))
    
    conn.commit()
    conn.close()
    return True, "🎉 プレミアム会員登録が完了しました！無制限チャットをお楽しみください。"

def get_user_premium(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_premium FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return bool(row["is_premium"])
    return False

def set_user_premium_direct(user_id, is_premium):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_premium = ? WHERE user_id = ?", (int(is_premium), user_id))
    conn.commit()
    conn.close()

def add_match(user_id, cast_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO matches (user_id, cast_id) VALUES (?, ?)", (user_id, cast_id))
    conn.commit()
    conn.close()

def get_matched_cast_ids(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT cast_id FROM matches WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [row["cast_id"] for row in rows]

def get_chat_count(user_id, cast_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT count FROM chat_counts WHERE user_id = ? AND cast_id = ?", (user_id, cast_id))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row["count"]
    return 0

def increment_chat_count(user_id, cast_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_counts (user_id, cast_id, count) VALUES (?, ?, 1)
        ON CONFLICT(user_id, cast_id) DO UPDATE SET count = count + 1
    """, (user_id, cast_id))
    conn.commit()
    conn.close()

def get_chat_history(user_id, cast_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, text FROM chat_messages 
        WHERE user_id = ? AND cast_id = ? 
        ORDER BY id ASC
    """, (user_id, cast_id))
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            "role": row["role"],
            "text": row["text"]
        })
    return history

def save_chat_message(user_id, cast_id, role, text):
    conn = get_db_connection