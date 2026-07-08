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

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

CAST_DATA_PATH = "cast_prompts_data.json"
IMAGE_DIR = "AIキャスト画像"
DB_PATH = "himakano.db"

st.set_page_config(page_title="ひまかのMatch", page_icon="💕", layout="centered")

# CSS（Tapple風に調整済み）
st.markdown("""
<style>
    .block-container { max-width: 440px !important; padding-top: 2rem; }
    .stButton button {
        width: 74px !important;
        height: 74px !important;
        border-radius: 50% !important;
        font-size: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

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
            is_premium INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            user_id TEXT,
            cast_id TEXT,
            PRIMARY KEY (user_id, cast_id)
        )
    """)
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
    return [row["cast_id"] for row in cursor.fetchall()]

def load_all_casts():
    with open(CAST_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_image_base64(path):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()

def main():
    init_db()
    if "swipe_index" not in st.session_state:
        st.session_state.swipe_index = 0

    casts = load_all_casts()
    if not casts:
        st.error("キャストデータが見つかりません")
        st.stop()

    # ==================== スワイプ画面 ====================
    st.markdown("### 🔍 好みのAIキャストを見つけよう！")

    filtered = casts  # 必要なら年齢フィルタを入れる

    if st.session_state.swipe_index >= len(filtered):
        st.session_state.swipe_index = 0

    cast = filtered[st.session_state.swipe_index]

    # 画像パス
    img_path = os.path.join(IMAGE_DIR, cast["id"], f"{cast['id']}_photo_1_main.png")
    img_src = get_image_base64(img_path) or "https://placehold.co/400x500?text=No+Image"

    # ==================== Tapple風カード（参考画像に近づけた版） ====================
    st.markdown(f"""
    <div style="
        max-width: 420px;
        margin: 0 auto;
        border-radius: 24px;
        overflow: hidden;
        box-shadow: 0 12px 32px rgba(0,0,0,0.18);
        background: white;
    ">
        <!-- 写真 -->
        <img src="{img_src}" style="width:100%; display:block; border-radius: 24px 24px 0 0;">

        <!-- 情報エリア -->
        <div style="padding: 16px 18px; background: white;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div>
                    <span style="font-size: 26px; font-weight: 700;">{cast['name']}</span>
                    <span style="font-size: 20px; color: #555; margin-left: 6px;">{cast['age']}歳</span>
                </div>
                <div style="
                    background: #ff4b4b;
                    color: white;
                    font-size: 13px;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-weight: bold;
                ">
                    {cast.get('job', '一般事務')}
                </div>
            </div>

            <!-- 自己紹介（短め） -->
            <div style="font-size: 15px; color: #333; line-height: 1.5;">
                {cast.get('first_message', 'はじめまして！よろしくお願いします。')}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    # いいね × ボタン（参考画像と同じ位置・サイズ感）
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✕", key="skip", use_container_width=True):
            st.session_state.swipe_index += 1
            st.rerun()
    with col2:
        if st.button("❤️", key="like", use_container_width=True):
            add_match("guest_user", cast["id"])
            st.success(f"{cast['name']}ちゃんとマッチしました！")
            st.session_state.swipe_index += 1
            st.rerun()

if __name__ == "__main__":
    main()