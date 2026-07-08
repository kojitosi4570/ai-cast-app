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
# ＝====================================================================
COMPANY_NAME = "合同会社小嶋企画"
REPRESENTATIVE = "小嶋"
ADDRESS = "神奈川県川崎市中原区..."
CONTACT_EMAIL = "kojitosi4570@gmail.com"
# =====================================================================

# 📱 スマホ専用画面に最適化
st.set_page_config(
    page_title="AIキャスト チャット", 
    page_icon="💬", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# 🎨 スマホ表示を極限まで美しくするカスタムCSS（丸型グラデーションボタンの搭載）
st.markdown("""
    <style>
        [data-testid='collapsedControl'] { display: none; }
        .block-container { padding-top: 5.0rem !important; padding-bottom: 2rem; max-width: 450px !important; }
        .stNotification { display: none !important; } 
        
        /* ① タップル風プロフィールカードの装飾 */
        .tapple-card {
            background-color: #ffffff;
            border-radius: 24px;
            border: 1px solid #f0f0f0;
            padding: 20px;
            box-shadow: 0px 8px 24px rgba(0,0,0,0.03);
            margin-top: 15px;
            margin-bottom: 20px;
        }
        .tapple-name {
            font-size: 24px;
            font-weight: bold;
            color: #111111;
            margin-bottom: 4px;
        }
        .tapple-badge {
            display: inline-block;
            background-color: #ff4b4b;
            color: white;
            font-size: 11px;
            font-weight: bold;
            padding: 3px 10px;
            border-radius: 20px;
            margin-bottom: 12px;
        }
        .tapple-desc {
            font-size: 14px;
            color: #444444;
            line-height: 1.6;
        }

        /* ② マッチング成立画面の演出 */
        .match-popup {
            background: linear-gradient(135deg, #ff758c 0%, #ff7eb3 100%);
            border-radius: 24px;
            padding: 30px;
            text-align: center;
            color: white;
            box-shadow: 0px 10px 30px rgba(255,118,140,0.3);
            margin-bottom: 25px;
        }
        .match-title {
            font-size: 22px;
            font-weight: bold;
            margin-bottom: 20px;
            text-shadow: 0px 2px 4px rgba(0,0,0,0.1);
        }
        
        /* ③ 通常の課金カード */
        .premium-card {
            background-color: #fffaf0;
            padding: 20px;
            border-radius: 20px;
            border: 2px solid #ffd700;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.05);
        }

        /* ④ ❌ と ❤️ の超洗練された丸型ベクターデザインボタン（CSSでStreamlit標準ボタンを完全上書き） */
        div[data-testid="column"]:nth-of-type(1) div.stButton > button {
            background-color: #ffffff !important;
            color: #ff5252 !important;
            font-size: 32px !important;
            border-radius: 50% !important;
            width: 72px !important;
            height: 72px !important;
            margin: 0 auto !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            border: 1px solid #f2f2f2 !important;
            box-shadow: 0px 8px 24px rgba(0,0,0,0.08) !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="column"]:nth-of-type(1) div.stButton > button:active {
            transform: scale(0.9) !important;
            background-color: #f7f7f2 !important;
        }
        
        div[data-testid="column"]:nth-of-type(2) div.stButton > button {
            background: linear-gradient(135deg, #ff5252 0%, #ff7eb3 100%) !important;
            color: #ffffff !important;
            font-size: 32px !important;
            border-radius: 50% !important;
            width: 72px !important;
            height: 72px !important;
            margin: 0 auto !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            border: none !important;
            box-shadow: 0px 8px 24px rgba(255,82,82,0.25) !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="column"]:nth-of-type(2) div.stButton > button:active {
            transform: scale(0.9) !important;
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
# 4. 👤 キャストデータの読み込み & 🖼️ 画像Base64変換（サーバー読込対策）
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
    """Renderなどのサーバー上でiframe内に確実に画像を読み込ませるためのBase64エンコード処理"""
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/png;base64,{encoded_string}"
    except Exception:
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

    # 💳 Stripe決済完了チェック
    query_params = st.query_params
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
                    st.query_params.clear()
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

    # 💓 1. マッチング成立お祝いポップアップ演出
    if st.session_state.last_matched_cast:
        matched_cast = st.session_state.last_matched_cast
        
        st.markdown(f"""
            <div class="match-popup">
                <div class="match-title">🎉 おめでとうございます！<br>マッチングが成立しました！</div>
            </div>
        """, unsafe_allow_html=True)
        
        # あなた（シルエット） ── (❤️) ── キャストの顔
        col_p1, col_p2, col_p3 = st.columns([1, 0.8, 1])
        with col_p1:
            st.image("https://placehold.co/150x150/1e88e5/ffffff?text=YOU", use_container_width=True, caption="あなた")
        with col_p2:
            st.markdown("<h1 style='text-align:center; color:#ff4b4b; padding-top:20px;'>❤️</h1>", unsafe_allow_html=True)
        with col_p3:
            img_path = os.path.join(IMAGE_DIR, matched_cast['id'], f"{matched_cast['id']}_photo_1_main.png")
            if os.path.exists(img_path):
                st.image(img_path, use_container_width=True, caption=matched_cast['name'])
            else:
                st.image("https://placehold.co/150x150?text=AI+Cast", use_container_width=True, caption=matched_cast['name'])
                
        st.markdown("<br>", unsafe_allow_html=True)
        
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
        st.markdown("### 🔍 好みのAIキャストを見つけよう！")
        
        # お好み詳細検索
        with st.expander("⚙️ お好み詳細検索（年齢・地域で絞り込み）"):
            filter_age = st.slider("年齢層の選択", 18, 45, (18, 35))
            filter_region = st.selectbox("探したい地域", ["制限なし（関東・東京エリア）", "東京（元住吉周辺など含む）", "神奈川"])
            
        filtered_casts = []
        for c in casts:
            if filter_age[0] <= c["age"] <= filter_age[1]:
                filtered_casts.append(c)
            
        if not filtered_casts:
            st.info("条件に一致するお相手が現在見つかりません。")
            return
            
        if st.session_state.swipe_index >= len(filtered_casts):
            st.session_state.swipe_index = 0
            
        active_cast = filtered_casts[st.session_state.swipe_index]
        c_id = active_cast["id"]
        
        # 📸 5枚の写真パスを用意してBase64化（表示のチカチカ・遅延を完全にゼロにします）
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

        # 👑 【究極進化：タップル風HTML/JSフォトスライダー】
        # 左右タップエリアの完全対応＆上部の5本線インジケーター同期システム
        slider_html = f"""
        <div class="slider-wrapper" style="position: relative; width: 100%; max-width: 420px; height: 480px; border-radius: 28px; overflow: hidden; background-color: #000; box-shadow: 0px 10px 30px rgba(0,0,0,0.15); margin: 0 auto;">
            <!-- 5本線の進捗インジケーター -->
            <div class="indicator-bar" style="position: absolute; top: 12px; left: 0; width: 100%; display: flex; justify-content: center; gap: 5px; z-index: 10; padding: 0 16px; box-sizing: border-box;">
                <div class="bar" id="b-0" style="flex: 1; height: 3px; background-color: #ffffff; border-radius: 2px; transition: all 0.2s;"></div>
                <div class="bar" id="b-1" style="flex: 1; height: 3px; background-color: rgba(255,255,255,0.4); border-radius: 2px; transition: all 0.2s;"></div>
                <div class="bar" id="b-2" style="flex: 1; height: 3px; background-color: rgba(255,255,255,0.4); border-radius: 2px; transition: all 0.2s;"></div>
                <div class="bar" id="b-3" style="flex: 1; height: 3px; background-color: rgba(255,255,255,0.4); border-radius: 2px; transition: all 0.2s;"></div>
                <div class="bar" id="b-4" style="flex: 1; height: 3px; background-color: rgba(255,255,255,0.4); border-radius: 2px; transition: all 0.2s;"></div>
            </div>
            
            <!-- スライドトラック -->
            <div class="track" id="track" style="width: 100%; height: 100%; display: flex; transition: transform 0.3s cubic-bezier(0.25, 1, 0.5, 1);">
                <img src="{img_srcs[0]}" style="width: 100%; height: 100%; object-fit: cover; flex-shrink: 0;" />
                <img src="{img_srcs[1]}" style="width: 100%; height: 100%; object-fit: cover; flex-shrink: 0;" />
                <img src="{img_srcs[2]}" style="width: 100%; height: 100%; object-fit: cover; flex-shrink: 0;" />
                <img src="{img_srcs[3]}" style="width: 100%; height: 100%; object-fit: cover; flex-shrink: 0;" />
                <img src="{img_srcs[4]}" style="width: 100%; height: 100%; object-fit: cover; flex-shrink: 0;" />
            </div>
            
            <!-- 左右透明なタップエリア -->
            <div class="tap-left" onclick="prev()" style="position: absolute; top: 0; left: 0; width: 40%; height: 100%; z-index: 5; cursor: pointer;"></div>
            <div class="tap-right" onclick="next()" style="position: absolute; top: 0; right: 0; width: 60%; height: 100%; z-index: 5; cursor: pointer;"></div>
        </div>
        
        <script>
            let idx = 0;
            const limit = 5;
            const tr = document.getElementById('track');
            
            function refresh() {{
                tr.style.transform = `translateX(${{-idx * 100}}%)`;
                for (let i = 0; i < limit; i++) {{
                    const bar = document.getElementById(`b-${{i}}`);
                    if (i === idx) {{
                        bar.style.backgroundColor = '#ffffff';
                    }} else {{
                        bar.style.backgroundColor = 'rgba(255,255,255,0.4)';
                    }}
                }}
            }}
            
            function next() {{
                if (idx < limit - 1) {{
                    idx++;
                    refresh();
                }}
            }}
            
            function prev() {{
                if (idx > 0) {{
                    idx--;
                    refresh();
                }}
            }}
        </script>
        """
        
        # iframe上にスライダーを表示（高さ・余白を調整）
        components.html(slider_html, height=490)

        # 👑 タップル風プロフィールカード
        st.markdown(f"""
            <div class="tapple-card">
                <div class="tapple-name">{active_cast['name']} ({active_cast['age']}歳)</div>
                <div class="tapple-badge">💼 {active_cast['job']} &nbsp;•&nbsp; 📍 元住吉（神奈川）周辺</div>
                <p class="tapple-desc">{active_cast['profile_text']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # ❌ スキップ（バツ） と ❤️ いいね！ の丸型特製アイコンボタン
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("✕", key="skip_btn", use_container_width=True):
                st.session_state.swipe_index += 1
                st.rerun()
        with col_b2:
            if st.button("❤️", key="like_btn", use_container_width=True):
                add_match(USER_ID, c_id)
                st.session_state.last_matched_cast = active_cast
                st.rerun()


    # 💬 3. 【やり取り（チャット）】画面
    elif st.session_state.current_tab == "💬 やりとり":
        matched_ids = get_matched_cast_ids(USER_ID)
        
        if not matched_ids:
            st.info("💡 まだマッチングしているお相手がいません。")
            st.write("上の「🔍 お相手を探す」タブから、気になるお相手をスワイプして『いいかも！』してみましょう！")
            return
            
        matched_casts = [c for c in casts if c["id"] in matched_ids]
        
        # 👥 マッチング中のお相手（丸型アイコン写真の横並び選択UI）
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
                5. 会話を一方的に受け止めて終わらせるのではなく、返答の最後には、必ず相手に「〇〇さんはどうですか？😊」や「普段はどのへんで観てるんですか？♪」といった【自然な質問や問いかけ】を1つ入れて、相手が返信しやすいフックを作ってください。
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