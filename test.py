import streamlit as st
import random
import os
import time  
import pandas as pd
import xml.etree.ElementTree as ET
import requests

# =====================================================================
# ★ 新機能：予算管理システム（ローカルで生成回数をカウント）
# =====================================================================
BUDGET_LIMIT_YEN = 10000  # 社長指定：1万円で絶対ストップ！
COST_PER_CAST = 1.5      # 1人生成するごとの推定コスト（円）
USAGE_FILE = "usage_count.txt" # 使用回数を記録する裏ファイル

def get_current_usage():
    if not os.path.exists(USAGE_FILE):
        return 0
    try:
        with open(USAGE_FILE, "r") as f:
            return int(f.read().strip())
    except:
        return 0

def increment_usage():
    current = get_current_usage()
    with open(USAGE_FILE, "w") as f:
        f.write(str(current + 1))

# =====================================================================
# 1. 【データ層】Excelから本番キャストデータを読み込み
# =====================================================================
def load_cast_master_from_excel():
    excel_file = "cast_master_list.xlsx"
    if not os.path.exists(excel_file):
        st.error(f"⚠️ エラー: 本番用のExcelファイル「{excel_file}」が同じフォルダに見つかりません！")
        return []
    try:
        df = pd.read_excel(excel_file)
        cast_list = []
        real_local_areas = [
            "川崎市武蔵小杉駅", "川崎市鹿島田駅", "川崎市元住吉駅", "川崎市溝の口駅", 
            "川崎市川崎駅", "横浜市日吉駅", "横浜市綱島駅", "横浜市菊名駅", 
            "横浜市新横浜駅", "さいたま市大宮駅", "川越市川越駅"
        ]
        for idx, row in df.iterrows():
            if pd.isna(row.get("名前")):
                continue
            area_index = idx % len(real_local_areas)
            assigned_area = real_local_areas[area_index]
            cast_list.append({
                "name": str(row.get("名前", "名無し")).strip(),
                "age": str(row.get("年齢", "20")).split('.')[0].strip(),
                "job": str(row.get("職業", "不明")).strip(),
                "char_type": str(row.get("キャラクタータイプ", "普通")).strip(), 
                "look_type": str(row.get("見た目系統", "普通系")).strip(),
                "station": assigned_area 
            })
        return cast_list
    except Exception as e:
        st.error(f"⚠️ Excel読み込みエラー: {e}")
        return []

# =====================================================================
# 2. 【ニュース層】Yahoo!ニュースから最新ニュースを取得
# =====================================================================
def get_multiple_trending_news():
    url = "https://news.yahoo.co.jp/rss/topics/top-picks.xml"
    news_candidates = []
    try:
        response = requests.get(url, timeout=5)
        root = ET.fromstring(response.content)
        ng_words = ["殺", "逮捕", "死亡", "遺体", "事件", "事故", "死", "容疑", "天気", "交通"]
        for item in root.findall('.//item'):
            title = item.find('title').text
            if not any(ng_word in title for ng_word in ng_words):
                clean_title = title.replace("【", "「").replace("】", "」")
                news_candidates.append(clean_title)
    except:
        pass
    if not news_candidates:
        news_candidates = ["大谷選手がまた特大ホームランを放ち驚異的な記録を更新中", "日本の主要株価が急変動、経済ニュースで投資家の注目集まる", "最新のAI技術を搭載したスマホアプリが世界中でトレンドに"]
    return "\n".join([f"- {title}" for title in news_candidates[:8]])

# =====================================================================
# 3. 【ロジック層】定型文メッセージ（バックアップ）
# =====================================================================
def generate_base_first_message(user_name, look_type):
    if "ギャル" in look_type or "グラドル" in look_type:
        return f"「はじめましてー！マッチありがとう✨ {user_name}さんって普段どのへんで飲むことが多いですかー？」"
    return f"「はじめまして！マッチできて嬉しいです✨ {user_name}さんは普段どのへんで遊ぶことが多いんですか？」"

def generate_base_second_message(user_name, char_type):
    return f"「{user_name}さんお仕事お疲れ様！私、周りから『合法の人間ビーズクッション』って呼ばれるくらいモチモチで癒やし系らしいから、疲れてたら1回ダイブしてみる？最近ちゃんと夜眠れてますか？」"

def generate_base_third_message(user_name, char_type, job):
    return f"「あ、いいですね！焼き鳥とかめっちゃ好きです。\nあ、やばい、今からミーティングだったの忘れてた💦 ちょっと行ってきます！\n仕事だるいしサボっちゃいたいなー。{user_name}さんは今日仕事サボったりしてないですか？」"

# =====================================================================
# 4. 【AI文章生成層】Grok呼び出し
# =====================================================================
def ask_grok_ai(prompt):
    time.sleep(1.5)
    api_key = st.secrets["XAI_API_KEY"]
    url = "https://api.x.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    safe_prompt = prompt.encode('utf-8', errors='ignore').decode('utf-8')
    payload = {
        "model": "grok-4.3",
        "messages": [{"role": "user", "content": safe_prompt}],
        "temperature": 0.7,
        "max_tokens": 120
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
    except:
        pass
    return None

# =====================================================================
# 5. 【UI層】Web画面の構築
# =====================================================================
st.set_page_config(page_title="小嶋企画 AIキャスト 鉄壁防衛版", layout="centered")

st.title("🤖 小嶋企画 AIチャットエンジン")

# --- 予算状況の表示 ---
current_usage_count = get_current_usage()
current_cost = current_usage_count * COST_PER_CAST
st.caption(f"💰 現在の推定API利用額: 約 {current_cost:.1f} 円 / 上限 {BUDGET_LIMIT_YEN} 円")

casts = load_cast_master_from_excel()
if not casts:
    st.stop()

cast_options = [f"{c['name']} ({c['age']}) - {c['job']}" for c in casts]
selected_option = st.selectbox("👩‍🦰 メッセージを作る女の子を選んでください", cast_options)
user_name = st.text_input("相手のユーザー名", "小嶋")

if st.button("▶︎ 選択した女の子のチャットを生成", type="primary"):
    
    # 🚨 【ストッパー発動】予算オーバーのチェック
    if current_cost >= BUDGET_LIMIT_YEN:
        st.error(f"🛑 【緊急停止】設定された予算上限（{BUDGET_LIMIT_YEN}円）に達しました！安全のためAI生成をロックしています。")
        st.stop()
        
    news_list_text = get_multiple_trending_news()
    selected_index = cast_options.index(selected_option)
    cast = casts[selected_index]
    
    st.subheader(f"👩‍🦰 {cast['name']} ({cast['age']}歳 / {cast['job']} / {cast['look_type']} / 📍最寄り:{cast['station']})")
    
    char_instruction = (
        f"【あなたの固有キャラクター性格】：あなたの性格・言動スタイルは「{cast['char_type']}」です。\n"
        f"ただのタメ口ではなく、この性格の特徴を言葉遣いや語尾、文章のテンポに【極限まで強く反映】させて七変化させてください。全員一律のありきたりな文章は厳禁です。"
    )
    
    # --- 1通
