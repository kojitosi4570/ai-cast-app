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

# ==================== ここから下は今までと同じ ====================

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

CAST_DATA_PATH = "cast_prompts_data.json"
IMAGE_DIR = "AIキャスト画像"
DB_PATH = "himakano.db"

COMPANY_NAME = "合同会社小嶋企画"
REPRESENTATIVE = "小嶋"
ADDRESS = "神奈川県川崎市中原区..."
CONTACT_EMAIL = "kojitosi4570@gmail.com"

st.set_page_config(
    page_title="AIキャスト チャット", 
    page_icon="💬", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# CSS（前回送ったやつをそのまま使用）
st.markdown("""
    <style>
        [data-testid='collapsedControl'] { display: none; }
        .block-container { padding-top: 5.0rem !important; padding-bottom: 2rem; max-width: 450px !important; }
        .stNotification { display: none !important; } 
        div[data-testid="column"] { display: flex !important; justify-content: center !important; align-items: center !important; }
        
        div[data-testid="column"]:nth-of-type(1) div.stButton > button {
            color: transparent !important;
            background-color: #ffffff !important;
            background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%23ff4d4d" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>') !important;
            background-size: 28px 28px !important;
            background-position: center !important;
            background-repeat: no-repeat !important;
            border-radius: 50% !important;
            width: 74px !important;
            height: 74px !important;
            border: 1px solid #eeeeee !important;
            box-shadow: 0px 8px 24px rgba(0,0,0,0.08) !important;
        }
        div[data-testid="column"]:nth-of-type(2) div.stButton > button {
            color: transparent !important;
            background-color: #ffffff !important;
            background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23ff4d4d" stroke="none"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>') !important;
            background-size: 28px 28px !important;
            background-position: center !important;
            background-repeat: no-repeat !important;
            border-radius: 50% !important;
            width: 74px !important;
            height: 74px !important;
            border: 1px solid #eeeeee !important;
            box-shadow: 0px 8px 24px rgba(255,65,108,0.3) !important;
        }
    </style>
""", unsafe_allow_html=True)

# ここから下はデータベース関数など（前回と同じ内容をそのまま入れておく）
# ※長くなるので、必要なら「全部送って」と言うか、部分的に調整するよ

# ...（データベース関数、Gemini関数などは前回の完全版と同じまま）

def main():
    # ここに前回の完全な main() 関数を入れる
    # （スワイプ画面はすでにTapple風に修正済み）

    if not API_KEY:
        st.error("APIキーが読み込めていません")
        st.stop()

    init_db()
    # ...（以降は前回送った完全版と同じ内容）

if __name__ == "__main__":
    main()