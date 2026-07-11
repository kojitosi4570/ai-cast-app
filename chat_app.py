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
# 1. 2大ボタン（スキップ🌀、いいね❤️）のサイズ差（強弱）と完璧な横並び・浮遊固定（position: fixed）
# 2. Streamlitボタンの余計な「四角い枠線（囲い）」「背景色」を!importantで100%完全に消去
# 3. 写真（HTMLスライダー）と、下にあるボタンの隙間をマイナスマージン（margin-top: -45px）でピタッと吸い寄せ！
st.markdown("""
    <style>
        [data-testid='collapsedControl'] { display: none; }
        .block-container { padding-top: 5.0rem !important; padding-bottom: 9rem !important; max-width: 450px !important; }
        .stNotification { display: none !important; } 
        
        /* 🚨 ボタンの親コンテナを画面最下部に完全に浮遊固定（スクロールしても常についてきます） */
        div[data-testid="column"] {
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            position: fixed !important;
            bottom: 30px !important;
            z-index: 99999 !important;
            width: 180px !important;
        }
        
        /* 左のボタン用カラムの固定位置 */
        div[data-testid="column"]:nth-of-type(1) {
            left: calc(50% - 130px) !important;
        }
        /* 右のボタン用カラムの固定位置 */
        div[data-testid="column"]:nth-of-type(2) {
            left: calc(50% + 15px) !important;
        }

        /* 🌀 スピンボタン（1列目・直径64px）：白地の正円＋水色の渦巻きマーク（SVG）に100%上書き（四角い枠線は完全に消去） */
        div[data-testid="column"]:nth-of-type(1) div.stButton > button {
            color: transparent !important;
            background-color: #ffffff !important;
            background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%2338bdf8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 10 10c0-1.7-.3-3.2-1-4.7L19 9c.6.9 1 2 1 3a8 8 0 1 1-8-8c1.3 0 2.5.3 3.6 1L14 6c-.6-.4-1.3-.6-2-.6a6 6 0 1 0 6 6c0-.4-.1-.8-.3-1.2L16 11c0 .2.1.5.1.8a4 6 0 1 1-4-4c.4 0 .7.1 1 .2"/></svg>') !important;
            background-size: 26px 26px !important;
            background-position: center !important;
            background-repeat: no-repeat !important;
            border-radius: 50% !important;
            width: 64px !important;
            height: 64px !important;
            min-width: 64px !important;
            max-width: 64px !important;
            min-height: 64px !important;
            max-height: 64px !important;
            border: 1px solid #eeeeee !important;
            box-shadow: 0px 8px 24px rgba(0,0,0,0.08) !important;
            transition: all 0.15s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
            margin: 0 auto !important;
        }
        div[data-testid="column"]:nth-of-type(1) div.stButton > button:active {
            transform: scale(0.90) !important;
            background-color: #f7f7f7 !important;
        }
        
        /* ❤️ いいねボタン（2列目・直径78pxの大物サイズ）：赤ピンクグラデーション正円＋純白ハートマーク（SVG）に100%上書き（四角い枠線は完全に消去） */
        div[data-testid="column"]:nth-of-type(2) div.stButton > button {
            color: transparent !important;
            background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%) !important;
            background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23ffffff" stroke="none"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>') !important;
            background-size: 32px 32px !important;
            background-position: center !important;
            background-repeat: no-repeat !important;
            border-radius: 50% !important;
            width: 78px !important;
            height: 78px !important;
            min-width: 78px !important;
            max-width: 78px !important;
            min-height: 78px !important;
            max-height: 78px !important;
            border: none !important;
            box-shadow: 0px 8px 24px rgba(255,65,108,0.3) !important;
            transition: all 0.15s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
            margin: 0 auto !important;
        }
        div[data-testid="column"]:nth-of-type(2) div.stButton > button:active {
            transform: scale(0.90) !important;
            opacity: 0.95 !important;
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
    
    # ゲストIDを正規メールアドレスに書き換え（履歴・マッチング履歴を引き継ぎます）
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
    """データベースから過去の会話履歴を安全に読み込みます"""
    conn = get_db_connection()
    cursor = conn.cursor()
    # 🛡️ 修正完了：(user_id, cast_id) を100%完璧にバインドしてバインディングエラーを永久解決
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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_messages (user_id, cast_id, role, text) 
        VALUES (?, ?, ?, ?)
    """, (user_id, cast_id, role, text))
    conn.commit()
    conn.close()


def clear_all_test_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM chat_counts")
    cursor.execute("DELETE FROM chat_messages")
    cursor.execute("DELETE FROM matches")
    conn.commit()
    conn.close()


# =====================================================================
# 3. 🤖 Geminiへのリクエスト関数（超安定・マルチターン規格）
# =====================================================================
def call_gemini_chat_engine(system_instruction, chat_history):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    
    contents = []
    for i, h in enumerate(chat_history):
        role = "user" if h["role"] == "user" else "model"
        if i == 0 and role == "model":
            contents.append({
                "role": "user",
                "parts": [{"text": "（あなたからいいね！を送りました）"}]
            })
        contents.append({
            "role": role,
            "parts": [{"text": h["text"]}]
        })
    
    body = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "generationConfig": {
            "temperature": 0.85,
            "maxOutputTokens": 350
        }
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req) as res:
            response_json = json.loads(res.read().decode("utf-8"))
            candidates = response_json.get("candidates", [])
            if not candidates:
                return "（ごめんね、ちょっと電波が悪いのかな…？メッセージ届いてるかな？😊）"
                
            first_candidate = candidates[0]
            finish_reason = first_candidate.get("finishReason", "")
            if finish_reason == "SAFETY" or finish_reason == "BLOCKLIST":
                return "（ごめんね、ちょっとお仕事の通知に気づくの遅れちゃった！お疲れさま😊）"
                
            content_data = first_candidate.get("content", {})
            parts = content_data.get("parts", [])
            
            if parts and "text" in parts[0]:
                return parts[0]["text"].strip()
            return "（あれ、ちょっと考え事しちゃってた。もう一回送ってもらえる？✨）"
                
    except Exception as e:
        print(f"Gemini APIエラー: {e}")
        return "（ごめんね、ちょっと通知に気づかなかった！もう一回送ってもらえる？😊）"


# =====================================================================
# 4. 👤 キャストデータの読み込み & Base64変換
# =====================================================================
def load_all_casts():
    possible_paths = ["cast_prompts_data.json", "npc_prompts_data.json"]
    target_path = None
    for path in possible_paths:
        if os.path.exists(path):
            target_path = path
            break
            
    if not target_path:
        st.error("❌ キャストデータが見つかりません。")
        st.stop()
        
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"❌ JSON解析失敗: {e}")
        st.stop()


def get_image_base64(path):
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/png;base64,{encoded_string}"
    except Exception as e:
        return ""


# =====================================================================
# ⚖️ 法的表示用の開閉アコーディオン表示関数（月額300円仕様）
# =====================================================================
def render_legal_documents():
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("⚖️ 特定商取引法に基づく表記"):
            st.markdown(f"""
            **【販売事業者名】**
            {COMPANY_NAME}
            
            **【運営責任者】**
            {REPRESENTATIVE}
            
            **【所在地】**
            {ADDRESS}
            
            **【連絡先メール】**
            {CONTACT_EMAIL}
            
            **【販売価格】**
            月額 300円（税込）
            
            **【対価の支払時期・方法】**
            支払時期：登録時、および翌月以降の自動更新時
            支払方法：クレジットカード決済（Stripe）
            
            **【役務の提供時期】**
            決済手続き完了後、即時にご利用可能
            
            **【キャンセル・返金について】**
            商品の性質上、決済完了後の返金・キャンセルには応じられません。
            解約はサイト内の設定画面よりいつでも手数料なしで行うことができます。
            """)
            
    with col2:
        with st.expander("📄 利用規約"):
            st.markdown(f"""
            **第1条（目的）**
            本サービスは、人工知能（LLM）技術を用いた架空のAIキャラクターとの疑似テキストコミュニケーションを楽しむ、健全なエンターテインメントWebアプリです。
            
            **第2条（AI自動応答に関する同意）**
            1. ユーザーは、当サービス内のすべての対話相手がAIシステムによって自動生成された架空のメッセージ（AI自動応答）であることに同意し、楽しむものとします。
            2. 本サービスは実在する人物との1対1の出会いを提供するマッチングアプリではなく、サクラや人間が偽ってメッセージを送る詐欺行為も一切排除しています。
            
            **第3条（プレミアム会員）**
            お試し無料回数（7往復）を超えてお喋りを楽しむ場合、月額300円（税込）のプレミアム会員プランへのご登録が必要です。
            
            **第4条（禁止事項）**
            不自然な嫌がらせ、不正利用、他者へのアカウント譲渡行為は一律禁止いたします。
            """)


# =====================================================================
# 💳 Stripe Checkout 決済セッション作成関数
# =====================================================================
def create_stripe_checkout_session(user_id):
    if not stripe or not STRIPE_SECRET_KEY:
        st.error("⚠️ StripeのAPIキーが登録されていないか、ライブラリがインストールされていません。")
        return None
        
    try:
        base_url = "https://ai-cast-app.onrender.com"
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'jpy',
                    'product_data': {
                        'name': 'プレミアムプラン（お喋り無制限）',
                        'description': 'AIキャストたちと制限なしで自由にお喋りを楽しめます。',
                    },
                    'unit_amount': 300,
                    'recurring': {
                        'interval': 'month',
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{base_url}/?session_id={{CHECKOUT_SESSION_ID}}&user_id_verify={user_id}",
            cancel_url=f"{base_url}/",
        )
        return session.url
    except Exception as e:
        st.error(f"❌ Stripeセッション作成失敗: {e}")
        return None


# =====================================================================
# 5. 🎨 Streamlit 画面表示・メインロジック（スワイプ ＆ チャット横並び連動）
# =====================================================================
def main():
    if not API_KEY:
        st.error("🔑 .env から APIキーが読み込めていません。")
        st.stop()

    init_db()

    # 🔑 端末用ゲストアカウント
    if "guest_id" not in st.session_state:
        st.session_state.guest_id = "guest_" + hashlib.md5(os.urandom(16)).hexdigest()[:8]
        
    GUEST_ID = st.session_state.guest_id
    create_guest_user(GUEST_ID)

    if "active_user_id" not in st.session_state:
        st.session_state.active_user_id = GUEST_ID

    USER_ID = st.session_state.active_user_id

    # 💾 セッション状態の初期化
    if "swipe_index" not in st.session_state:
        st.session_state.swipe_index = 0  
    if "last_matched_cast" not in st.session_state:
        st.session_state.last_matched_cast = None  
    if "current_tab" not in st.session_state:
        st.session_state.current_tab = "🔍 お相手探し"
    if "active_chat_cast_id" not in st.session_state:
        st.session_state.active_chat_cast_id = None 

    query_params = st.query_params

    # 💳 Stripe決済完了チェック
    if "session_id" in query_params and "user_id_verify" in query_params:
        session_id = query_params["session_id"]
        user_verify = query_params["user_id_verify"]
        
        if stripe:
            try:
                checkout_session = stripe.checkout.Session.retrieve(session_id)
                if checkout_session.payment_status == "paid":
                    set_user_premium_direct(user_verify, True)
                    st.session_state.active_user_id = user_verify
                    st.success("🎉 お支払いが確認できました！プレミアム会員として無制限にお喋りをお楽しみください！")
                    # 🛡️ 解決：個別キー削除
                    if "session_id" in st.query_params: del st.query_params["session_id"]
                    if "user_id_verify" in st.query_params: del st.query_params["user_id_verify"]
                    st.rerun()
            except Exception as e:
                st.error(f"決済の検証中にエラーが発生しました: {e}")

    casts = load_all_casts()
    if not casts:
        st.warning("⚠️ キャストデータが空っぽです。")
        st.stop()

    # 📱 画面の切り替えタブ
    st.write(" ")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        if st.button("🔍 お相手を探す", use_container_width=True, type="primary" if st.session_state.current_tab == "🔍 お相手探し" else "secondary"):
            st.session_state.current_tab = "🔍 お相手探し"
            st.rerun()
    with col_t2:
        if st.button("💬 やりとり（チャット）", use_container_width=True, type="primary" if st.session_state.current_tab == "💬 やりとり" else "secondary"):
            st.session_state.current_tab = "💬 やりとり"
            st.rerun()

    # 💓 1. 【マッチング演出】「あなた ── ❤️ ── 女の子」がスマホでも絶対に縦に崩れない、横一列の美しいHTMLお祝いカード
    if st.session_state.last_matched_cast:
        matched_cast = st.session_state.last_matched_cast
        
        # 画像パスのBase64エンコード（ポップアップ画像も一瞬で表示させます）
        m_img_path = os.path.join(IMAGE_DIR, matched_cast['id'], f"{matched_cast['id']}_photo_1_main.png")
        b64_cast_img = get_image_base64(m_img_path)
        if not b64_cast_img:
            b64_cast_img = "https://placehold.co/150x150?text=AI+Cast"

        match_html = f"""
        <div class="match-popup" style="background: linear-gradient(135deg, #ff758c 0%, #ff7eb3 100%); border-radius: 24px; padding: 25px; text-align: center; color: white; box-shadow: 0px 10px 30px rgba(255,118,140,0.3); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <div class="match-title" style="font-size: 21px; font-weight: bold; margin-bottom: 25px; text-shadow: 0px 2px 4px rgba(0,0,0,0.1);">🎉 おめでとうございます！<br>マッチングが成立しました！</div>
            
            <!-- 🛡️ 解決策：CSS flexboxによる、スマホ縦潰れ防止の完璧な横一列（Row）配置 -->
            <div style="display: flex; justify-content: center; align-items: center; gap: 12px; margin-bottom: 20px; width: 100%;">
                <div style="flex: 1; text-align: center; max-width: 105px;">
                    <img src="https://placehold.co/150x150/1e88e5/ffffff?text=YOU" style="width: 100%; aspect-ratio: 1/1; border-radius: 50%; object-fit: cover; border: 3px solid white;" />
                    <div style="font-size: 11px; margin-top: 6px; font-weight: bold; opacity: 0.9;">あなた</div>
                </div>
                <div style="font-size: 32px; color: #ffffff; padding-bottom: 15px; animation: pulse 1s infinite;">❤️</div>
                <div style="flex: 1; text-align: center; max-width: 105px;">
                    <img src="{b64_cast_img}" style="width: 100%; aspect-ratio: 1/1; border-radius: 50%; object-fit: cover; border: 3px solid white;" />
                    <div style="font-size: 11px; margin-top: 6px; font-weight: bold; opacity: 0.9;">{matched_cast['name']}</div>
                </div>
            </div>
        </div>
        """
        components.html(match_html, height=270, scrolling=False)
        st.write(" ")
        
        if st.button(f"💬 {matched_cast['name']}ちゃんにメッセージを送る", type="primary", use_container_width=True):
            st.session_state.current_tab = "💬 やりとり"
            st.session_state.last_matched_cast = None
            st.session_state.active_chat_cast_id = matched_cast['id']
            st.rerun()
            
        if st.button("✕ 他のお相手も探す", use_container_width=True):
            st.session_state.last_matched_cast = None
            st.rerun()
            
        return


    # 💓 2. 【🔍 お相手を探す】スワイプ画面の実装
    if st.session_state.current_tab == "🔍 お相手探し":
        # 👑 【見出し】お気に入りのキャストを探そう
        st.markdown("### 🔍 お気に入りのキャストを探そう")
        
        # 👥 【PWA仕様】：スマホでも絶対に縦崩れしない、HTMLフレックスボックス横スクロール形式に一新！
        st.markdown("**✨ 本日のおすすめキャスト**")
        
        matched_ids = get_matched_cast_ids(USER_ID)
        unmatched_casts_all = [c for c in casts if c["id"] not in matched_ids]
        
        # 🛡️ 解決：スマホでも絶対に縦崩れしない、HTMLフレックスボックス横スクロール形式
        if unmatched_casts_all:
            # HTMLで横スクロール可能な丸写真一覧を構築
            recommend_html = """
            <div style="display: flex; flex-direction: row; gap: 15px; overflow-x: auto; padding: 10px 0; -webkit-overflow-scrolling: touch; -webkit-tap-highlight-color: transparent;">
            """
            for r_cast in unmatched_casts_all[:4]:
                r_img_path = os.path.join(IMAGE_DIR, r_cast["id"], f"{r_cast['id']}_photo_1_main.png")
                b64_img = get_image_base64(r_img_path)
                if not b64_img: b64_img = "https://placehold.co/72x72?text=AI"
                
                # 画像自体をクリックすると、その子のスワイプ画面へ直接ジャンプするAタグリンク
                recommend_html += f"""
                <div style="text-align: center; flex-shrink: 0; width: 75px;">
                    <a href="?rec_id={r_cast['id']}" target="_parent" style="text-decoration: none;">
                        <img src="{b64_img}" style="width: 72px; height: 72px; border-radius: 50%; object-fit: cover; border: 2px solid #eaeaea; box-shadow: 0 4px 10px rgba(0,0,0,0.05);" />
                    </a>
                </div>
                """
            recommend_html += "</div>"
            components.html(recommend_html, height=100, scrolling=False)
            
            # タップされたおすすめキャストを検知してスワイプ画面を合わせます
            if "rec_id" in query_params:
                rec_id = query_params["rec_id"]
                for idx_f, c_f in enumerate(unmatched_casts_all):
                    if c_f["id"] == rec_id:
                        st.session_state.swipe_index = idx_f
                        break
                if "rec_id" in st.query_params: del st.query_params["rec_id"]
                st.rerun()
                
        st.markdown("---")

        with st.expander("⚙️ お好み詳細検索（年齢・地域で絞り込み）"):
            filter_age = st.slider("年齢層の選択", 18, 45, (18, 35))
            filter_region = st.selectbox("探したい地域", ["制限なし（関東・東京エリア）", "東京（元住吉周辺など含む）", "神奈川"])
            
        # マッチングが成功している相手をスワイプ画面から「即座に自動除外」する絞り込み
        filtered_casts = []
        for c in casts:
            if filter_age[0] <= c["age"] <= filter_age[1] and c["id"] not in matched_ids:
                filtered_casts.append(c)
            
        if not filtered_casts:
            st.info("条件に一致する新しいお相手が現在見つかりません。")
            if st.button("🔄 データを初期化して最初からテストする", use_container_width=True):
                clear_all_test_data()
                st.session_state.clear()
                st.rerun()
            return
            
        if st.session_state.swipe_index >= len(filtered_casts):
            st.session_state.swipe_index = 0
            
        active_cast = filtered_casts[st.session_state.swipe_index]
        c_id = active_cast["id"]
        
        # 📸 5枚の写真パスを用意してBase64化
        photo_paths = [
            os.path.join(IMAGE_DIR, c_id, f"{c_id}_photo_1_main.png"),
            os.path.join(IMAGE_DIR, c_id, f"{c_id}_photo_2_sub.png"),
            os.path.join(IMAGE_DIR, c_id, f"{c_id}_photo_3_sub.png"),
            os.path.join(IMAGE_DIR, c_id, f"{c_id}_photo_4_sub.png"),
            os.path.join(IMAGE_DIR, c_id, f"{c_id}_photo_5_sub.png")
        ]
        
        img_srcs = []
        for p in photo_paths:
            b64 = get_image_base64(p)
            img_srcs.append(b64 if b64 else "https://placehold.co/400x500?text=AI+Cast+Image")

        # 👑 【スリムグラデーション仕様・一体型フォトスライダー（高さをさらに縦長：560pxに大迫力化！）】
        slider_html = f"""
        <div class="slider-wrapper">
            <!-- 5本線の進捗インジケーター -->
            <div style="position: absolute; top: 12px; left: 0; width: 100%; display: flex; justify-content: center; gap: 5px; z-index: 10; padding: 0 16px; box-sizing: border-box;">
                <div class="bar" id="b-0" style="flex: 1; height: 3px; background-color: #ffffff; border-radius: 2px; transition: all 0.2s;"></div>
                <div class="bar" id="b-1" style="flex: 1; height: 3px; background-color: rgba(255,255,255,0.4); border-radius: 2px; transition: all 0.2s;"></div>
                <div class="bar" id="b-2" style="flex: 1; height: 3px; background-color: rgba(255,255,255,0.4); border-radius: 2px; transition: all 0.2s;"></div>
                <div class="bar" id="b-3" style="flex: 1; height: 3px; background-color: rgba(255,255,255,0.4); border-radius: 2px; transition: all 0.2s;"></div>
                <div class="bar" id="b-4" style="flex: 1; height: 3px; background-color: rgba(255,255,255,0.4); border-radius: 2px; transition: all 0.2s;"></div>
            </div>
            
            <!-- スライド画像トラック -->
            <div class="track" id="track" style="width: 100%; height: 100%; display: flex; transition: transform 0.25s ease-out;">
                <img src="{img_srcs[0]}" style="width: 100%; height: 100%; object-fit: cover; flex-shrink: 0;" />
                <img src="{img_srcs[1]}" style="width: 100%; height: 100%; object-fit: cover; flex-shrink: 0;" />
                <img src="{img_srcs[2]}" style="width: 100%; height: 100%; object-fit: cover; flex-shrink: 0;" />
                <img src="{img_srcs[3]}" style="width: 100%; height: 100%; object-fit: cover; flex-shrink: 0;" />
                <img src="{img_srcs[4]}" style="width: 100%; height: 100%; object-fit: cover; flex-shrink: 0;" />
            </div>
            
            <!-- 左右タップエリア（完全にチカチカ白光りしないように設定） -->
            <div class="tap-left" onclick="prev()" style="position: absolute; top: 0; left: 0; width: 40%; height: 100%; z-index: 5; cursor: pointer;"></div>
            <div class="tap-right" onclick="next()" style="position: absolute; top: 0; right: 0; width: 60%; height: 100%; z-index: 5; cursor: pointer;"></div>

            <!-- 最下部スリムオーバーレイ（名前、年齢、お仕事タグの1行だけをスッキリ表示） -->
            <div class="profile-sheet-overlay">
                <div style="font-size: 22px; font-weight: bold; margin-bottom: 3px; text-shadow: 0px 1px 3px rgba(0,0,0,0.6);">{active_cast['name']} ({active_cast['age']}歳)</div>
                <div style="font-size: 11px; font-weight: bold; opacity: 0.95; text-shadow: 0px 1px 2px rgba(0,0,0,0.6);">💼 {active_cast['job']} &nbsp;•&nbsp; 📍 元住吉周辺</div>
            </div>
        </div>
        
        <script>
            let idx = 0;
            const limit = 5;
            const tr = document.getElementById('track');
            
            function refresh() {{
                tr.style.transform = `translateX(${{-idx * 100}}%)`;
                for (let i = 0; i < limit; i++) {{
                    const bar = document.getElementById(`b-${{i}}`);
                    if(bar) bar.style.backgroundColor = (i === idx) ? '#ffffff' : 'rgba(255,255,255,0.4)';
                }}
            }}
            
            function next() {{ if (idx < limit - 1) {{ idx++; refresh(); }} }}
            function prev() {{ if (idx > 0) {{ idx--; refresh(); }} }}
        </script>
        """
        
        # 写真スライダーを画面に埋め込み（高さを550pxに広げて縦長を強調）
        components.html(slider_html, height=550, scrolling=False)
        
        # 👑 【おじさん熱狂・完全解決仕様】：
        # データベースから直接、一瞬で「いいね・スキップ」を検知するPython純正ボタンに変更しました！
        # これにより、スマホのセキュリティ制限（CORS）を完全にバイパスし、押した瞬間に【100%確実に爆速で作動】します。
        # さらに、CSSの固定配置（position: fixed）によって、画面を下にスクロールしても丸ボタンは画面最下部に「常にプカプカ浮かんで固定追従」し続けます！
        st.write(" ")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("✕", key="skip_btn", use_container_width=True):
                # ユーザーがメッセージを送信した時
                st.session_state.swipe_index += 1
                st.rerun()
        with col_b2:
            if st.button("❤️", key="like_btn", use_container_width=True):
                add_match(USER_ID, c_id)
                st.session_state.last_matched_cast = active_cast
                st.rerun()

        # 👑 【お写真10割保護設計】自己紹介シートは、下にスクロール（展開）するとスッと現れる開閉アコーディオンに配置
        st.write(" ")
        with st.expander(f"📝 プロフィール"):
            st.markdown(f"""
            **【お相手紹介】**
            {active_cast['profile_text']}
            
            **【基本情報】**
            *   年齢: {active_cast['age']}歳
            *   職業: {active_cast['job']}
            *   地域: 神奈川県（元住吉周辺など含む）
            """)


    # 💬 3. 【やり取り（チャット）】画面
    elif st.session_state.current_tab == "💬 やりとり":
        matched_ids = get_matched_cast_ids(USER_ID)
        
        if not matched_ids:
            st.info("💡 まだマッチングしているお相手がいません。")
            st.write("上の「🔍 お相手を探す」タブから、気になるお相手をスワイプして『いいかも！』してみましょう！")
            return
            
        matched_casts = [c for c in casts if c["id"] in matched_ids]
        
        # 👥 マッチング中のお相手
        st.markdown("### 👥 マッチング中のお相手")
        
        if st.session_state.active_chat_cast_id not in matched_ids:
            st.session_state.active_chat_cast_id = matched_ids[0]
            
        num_cols = min(len(matched_casts), 4)
        cols = st.columns(num_cols)
        
        for idx, m_cast in enumerate(matched_casts[:4]):
            with cols[idx]:
                img_path = os.path.join(IMAGE_DIR, m_cast["id"], f"{m_cast['id']}_photo_1_main.png")
                
                if os.path.exists(img_path):
                    st.image(img_path, width=75)
                else:
                    st.image("https://placehold.co/75x75?text=AI", width=75)
                
                is_active = (st.session_state.active_chat_cast_id == m_cast["id"])
                btn_style = "primary" if is_active else "secondary"
                
                if st.button(f"{m_cast['name']}", key=f"sel_{m_cast['id']}", type=btn_style, use_container_width=True):
                    st.session_state.active_chat_cast_id = m_cast["id"]
                    st.rerun()
                    
        st.markdown("---")
        
        cast_id = st.session_state.active_chat_cast_id
        cast = next(c for c in matched_casts if c["id"] == cast_id)

        # 会話ログの取得
        is_premium = get_user_premium(USER_ID)
        current_count = get_chat_count(USER_ID, cast_id)
        chat_history = get_chat_history(USER_ID, cast_id)

        if not chat_history:
            save_chat_message(USER_ID, cast_id, "model", cast["first_message"])
            chat_history = get_chat_history(USER_ID, cast_id)

        st.markdown(f"**💬 {cast['name']} ({cast['age']}歳 / {cast['job']}) と会話中**")
        
        # チャット履歴描画
        for msg in chat_history:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(msg["text"])
            else:
                with st.chat_message("assistant"):
                    st.write(msg["text"])

        st.markdown("---")

        # 🚨 7往復制限
        if current_count >= 7 and not is_premium:
            st.warning("🔒 続きを話すにはプレミアム会員への登録が必要です。")
            
            st.markdown(
                """
                <div class="premium-card">
                    <h3 style="color: #b8860b; margin-top: 0; font-size: 18px;">👑 プレミアム会員になってお喋りを続けよう！</h3>
                    <p style="color: #666; font-size: 13px; margin-bottom: 10px;">
                        月額プレミアムプランに登録して、結愛ちゃんたちと無制限にチャットを楽しみましょう！
                    </p>
                    <h4 style="color: #d39e00; margin-bottom: 0; font-size: 18px;">💳 月額 300円（税込）</h4>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            reg_email = st.text_input("メールアドレス", placeholder="your-email@example.com")
            reg_password = st.text_input("パスワード", type="password", placeholder="6文字以上のパスワード")
            
            if st.button("💳 アカウント登録 ＆ クレジットカードで購入する（月額300円）", type="primary", use_container_width=True):
                if not reg_email or not reg_password:
                    st.error("⚠️ メールアドレスとパスワードを入力してください。")
                elif len(reg_password) < 6:
                    st.error("⚠️ パスワードは6文字以上で設定してください。")
                else:
                    success, msg = upgrade_guest_to_premium(USER_ID, reg_email, reg_password)
                    if success:
                        st.session_state.active_user_id = reg_email
                        if STRIPE_SECRET_KEY:
                            checkout_url = create_stripe_checkout_session(reg_email)
                            if checkout_url:
                                st.success("🎉 アカウントを作成しました！Stripeの決済ページへ移動します...")
                                st.markdown(f'<a href="{checkout_url}" target="_self" style="display:inline-block; background-color:#28a745; color:white; padding:10px 20px; text-decoration:none; border-radius:5px; font-weight:bold; width:100%; text-align:center;">💳 今すぐ決済を完了する</a>', unsafe_allow_html=True)
                        else:
                            set_user_premium_direct(reg_email, True)
                            st.success("🎉 アカウントを作成しました！")
                            st.rerun()
                    else:
                        st.error(msg)
                        
        else:
            if user_msg := st.chat_input("メッセージを送る..."):
                save_chat_message(USER_ID, cast_id, "user", user_msg)
                
                if not is_premium:
                    increment_chat_count(USER_ID, cast_id)

                clean_profile = cast['profile_text']
                clean_profile = clean_profile.replace("エロい", "魅力的な").replace("お胸", "抜群のスタイル").replace("下心", "関心")

                updated_history = get_chat_history(USER_ID, cast_id)

                system_instruction = f"""
                あなたはキャスト「{cast['name']}」（年齢: {cast['age']}歳、職業: {cast['job']}）という日本の実在する女性本人です。
                マッチング相手の男性とスマートフォンで優しく、お喋りを盛り上げる会話をしています。
                
                【あなたのプロフィール】
                {clean_profile}
                ・愛嬌がたっぷりあってお喋りが大好き、少しあざとくて男性の心を惹きつけるのが上手な魅力的な女性です。

                【絶対に守る会話のルール】
                1. あなたは実在する女性です。AI、LLM、自動応答、テンプレといった、機械的な存在を想起させるセリフは一律で完全禁止です。
                2. 丁寧で上品でありながら、親しみやすさを織り交ぜた優しい敬語（〜ですね、〜ですか？など）で接してください（タメ口は一律禁止です）。
                3. 「（笑）」や「笑」、「w」などのネット表現はサクラ感が出るため【一律で使用禁止】です。楽しさを表現する際は、自然な絵文字（😊、✨、♪）をメッセージに1〜2個程度、優しく落とすように使ってください。
                4. 相手の直前の発言を完璧に理解し、それに対するあなた自身の具体的な感想や共感、お茶目なリアクションを必ず1〜2文入れて返答してください。一言だけの淡白な返信は絶対にしないでください。
                5. 会話を一方的に受け止めて終わらせるのではない、返答の最高には、必ず相手に「〇〇さんはどうですか？😊」や「普段はどのへんで観てるんですか？♪」といった【自然な質問や問いかけ】を1つ入れて、相手が返信しやすいフックを作ってください。
                6. 返答は、スマホのチャット画面で最も読みやすい【120文字前後（3〜4文程度）】に整え、必ず文章の最後まで途切れることなく完結させて出力してください。
                """

                with st.spinner(f"{cast['name']}が入力中..."):
                    reply = call_gemini_chat_engine(system_instruction, updated_history)
                    
                save_chat_message(USER_ID, cast_id, "model", reply)
                st.rerun()

    # ⚖️ スマホ最下部に法的表示のアコーディオンを配置
    render_legal_documents()

    # 🛠️ 開発者用テストリセットツール
    st.markdown("---")
    with st.expander("🛠️ 開発者用テスト設定"):
        st.write(f"現在のゲストセッションID: `{GUEST_ID}`")
        st.write(f"現在のアクティブユーザーID: `{USER_ID}`")
        if st.button("🔄 データを完全に初期化して最初からテスト"):
            clear_all_test_data()
            st.session_state.clear()
            st.success("データベースとセッションが完全に初期化されました。")
            st.rerun()


if __name__ == "__main__":
    main()