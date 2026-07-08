import os
import json
import sqlite3
import base64
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

CAST_DATA_PATH = "cast_prompts_data.json"
IMAGE_DIR = "AIキャスト画像"
DB_PATH = "himakano.db"

st.set_page_config(page_title="ひまかのMatch", page_icon="💕", layout="centered")

st.markdown("""
<style>
    .block-container {
        max-width: 440px !important;
        padding-top: 1.5rem;
    }
    .stButton button {
        width: 78px !important;
        height: 78px !important;
        border-radius: 50% !important;
        font-size: 0px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
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

    # スワイプ画面
    st.markdown("### 🔍 好みのAIキャストを見つけよう！")

    if st.session_state.swipe_index >= len(casts):
        st.session_state.swipe_index = 0

    cast = casts[st.session_state.swipe_index]

    # 画像
    img_path = os.path.join(IMAGE_DIR, cast["id"], f"{cast['id']}_photo_1_main.png")
    img_src = get_image_base64(img_path) or "https://placehold.co/400x500?text=No+Image"

    # ==================== 参考画像に近いTapple風カード ====================
    st.markdown(f"""
    <div style="
        max-width: 420px;
        margin: 20px auto 0;
        border-radius: 24px;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(0,0,0,0.18);
        background: white;
    ">
        <!-- 写真 -->
        <img src="{img_src}" style="width:100%; display:block;">

        <!-- 情報エリア -->
        <div style="padding: 18px 20px 20px; background: white;">
            <!-- 名前・年齢・職業 -->
            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 10px;">
                <div>
                    <span style="font-size: 26px; font-weight: 700; color: #222;">{cast['name']}</span>
                    <span style="font-size: 20px; color: #555; margin-left: 6px;">{cast['age']}歳</span>
                </div>
                <div style="
                    background: #ff4b4b;
                    color: white;
                    font-size: 13px;
                    padding: 5px 14px;
                    border-radius: 20px;
                    font-weight: bold;
                    white-space: nowrap;
                ">
                    {cast.get('job', '一般事務')}
                </div>
            </div>

            <!-- 自己紹介（短め） -->
            <div style="font-size: 15px; color: #333; line-height: 1.6;">
                {cast.get('first_message', 'はじめまして！よろしくお願いします。')}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    # いいね × ボタン
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✕", key="skip_btn", use_container_width=True):
            st.session_state.swipe_index += 1
            st.rerun()
    with col2:
        if st.button("❤️", key="like_btn", use_container_width=True):
            add_match("guest_user", cast["id"])
            st.success(f"{cast['name']}ちゃんとマッチしました！")
            st.session_state.swipe_index += 1
            st.rerun()

if __name__ == "__main__":
    main()