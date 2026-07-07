import os
import json
import sqlite3
import hashlib
import urllib.request
import urllib.error
import streamlit as st
from dotenv import load_dotenv

# 📡 1. .env からAPIキーを自動読み込み
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

CAST_DATA_PATH = "cast_prompts_data.json"
IMAGE_DIR = "AIキャスト画像"
DB_PATH = "himakano.db"  # 💾 データベース

# 📱 スマホ専用画面に最適化
st.set_page_config(
    page_title="AIキャスト チャット", 
    page_icon="💬", 
    layout="centered", # 画面中央にスマホ幅でスッキリ収める
    initial_sidebar_state="collapsed" # スマホで邪魔になるサイドバーを最初から閉じる
)

# 🎨 スマホ表示をさらに美しく、チャット枠をLINE風に近づけるスタイリング
st.markdown("""
    <style>
        [data-testid="collapsedControl"] { display: none; }
        .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 450px !important; }
        .stNotification { display: none !important; } /* Streamlit公式の非推奨警告を画面上から完全に非表示にします */
        .premium-card {
            background-color: #fffaf0;
            padding: 20px;
            border-radius: 20px;
            border: 2px solid #ffd700;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.05);
        }
    </style>
""", unsafe_allow_html=True)


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
# 4. 👤 キャストデータの読み込み
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


# =====================================================================
# 5. 🎨 Streamlit 画面表示（スマホ縦画面完全特化）
# =====================================================================
def main():
    if not API_KEY:
        st.error("🔑 .env から APIキーが読み込めていません。")
        st.stop()

    init_db()

    if "guest_id" not in st.session_state:
        st.session_state.guest_id = "guest_" + hashlib.md5(os.urandom(16)).hexdigest()[:8]
        
    GUEST_ID = st.session_state.guest_id
    create_guest_user(GUEST_ID)

    if "active_user_id" not in st.session_state:
        st.session_state.active_user_id = GUEST_ID

    USER_ID = st.session_state.active_user_id

    casts = load_all_casts()
    if not casts:
        st.warning("⚠️ キャストデータが空っぽです。")
        st.stop()

    # 📱 最上部でのキャスト選択
    st.markdown("### 👤 キャストを選んでチャット開始")
    cast_names = [c["name"] for c in casts]
    selected_name = st.selectbox("", cast_names, label_visibility="collapsed")
    
    cast = next(c for c in casts if c["name"] == selected_name)
    cast_id = cast["id"]

    is_premium = get_user_premium(USER_ID)
    current_count = get_chat_count(USER_ID, cast_id)
    chat_history = get_chat_history(USER_ID, cast_id)

    if not chat_history:
        save_chat_message(USER_ID, cast_id, "model", cast["first_message"])
        chat_history = get_chat_history(USER_ID, cast_id)

    # 👑 キャスト写真・プロフィールのコンパクト表示（新しい警告の出ない書き方に変更）
    col1, col2 = st.columns([1, 1.8])
    with col1:
        img_path = os.path.join(IMAGE_DIR, cast_id, f"{cast_id}_photo_1_main.png")
        if os.path.exists(img_path):
            st.image(img_path, use_container_width=True) # 🟢 警告の出ない書き方に更新
        else:
            st.image("https://placehold.co/400x500?text=AI+Cast", use_container_width=True)
    with col2:
        st.markdown(f"**{cast['name']} ({cast['age']}歳 / {cast['job']})**")
        st.write(cast["profile_text"][:85] + "...") 

    st.markdown("---")

    # 💬 チャット履歴のLINE風描画
    for msg in chat_history:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["text"])
        else:
            with st.chat_message("assistant"):
                st.write(msg["text"])

    st.markdown("---")

    # 🚨 3. 3往復制限＆スマホ用会員登録・デモ決済フォーム
    if current_count >= 3 and not is_premium:
        st.warning("🔒 続きを話すにはプレミアム会員への登録が必要です。")
        
        st.markdown(
            """
            <div class="premium-card">
                <h3 style="color: #b8860b; margin-top: 0; font-size: 18px;">👑 プレミアム会員になってお喋りを続けよう！</h3>
                <p style="color: #666; font-size: 13px; margin-bottom: 10px;">
                    月額プレミアムプランに登録して、結愛ちゃんたちと無制限にチャットを楽しみましょう！
                </p>
                <h4 style="color: #d39e00; margin-bottom: 0; font-size: 18px;">💳 月額 500円（税込）</h4>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        reg_email = st.text_input("メールアドレス", placeholder="your-email@example.com")
        reg_password = st.text_input("パスワード", type="password", placeholder="6文字以上のパスワード")
        
        if st.button("👑 アカウント登録 ＆ クレジットカード決済（デモ）", type="primary", use_container_width=True):
            if not reg_email or not reg_password:
                st.error("⚠️ メールアドレスとパスワードを入力してください。")
            elif len(reg_password) < 6:
                st.error("⚠️ パスワードは6文字以上で設定してください。")
            else:
                success, msg = upgrade_guest_to_premium(USER_ID, reg_email, reg_password)
                if success:
                    st.session_state.active_user_id = reg_email
                    st.success(msg)
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