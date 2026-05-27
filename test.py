import streamlit as st
import random
import os
import time  
import pandas as pd
import xml.etree.ElementTree as ET
import requests

# =====================================================================
# 1. 【データ層】Excelからキャストデータを読み込む
# =====================================================================
def load_cast_master_from_excel():
    excel_file = "cast_master_list.xlsx"
    if not os.path.exists(excel_file):
        st.error(f"⚠️ エラー: {excel_file} が見つかりません！")
        return []
    df = pd.read_excel(excel_file)
    cast_list = []
    for _, row in df.iterrows():
        cast_list.append({
            "name": str(row.get("名前", "名無し")),
            "age": str(row.get("年齢", "20")),
            "job": str(row.get("職業", "不明")),
            "char_type": str(row.get("キャラクタータイプ", "普通")), 
            "look_type": str(row.get("見た目系統", "普通系"))
        })
    return cast_list

# =====================================================================
# 2. 【ニュース層】Yahoo!ニュースから複数の最新ニュースの候補をまとめて取得
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
    
    # ニュースが取れなかった時のためのバックアップ
    if not news_candidates:
        news_candidates = [
            "大谷選手がまた特大ホームランを放ち驚異的な記録を更新中",
            "日本の主要株価が急変動、経済ニュースで投資家の注目集まる",
            "最新のAI技術を搭載したスマホアプリが世界中でトレンドに",
            "今年の最新トレンドファッションや注目ブランドが発表"
        ]
    
    # 上位8件のニュースをテキストの箇条書きにしてAIに選ばせる
    return "\n".join([f"- {title}" for title in news_candidates[:8]])

# =====================================================================
# 3. 【ロジック層】定型文メッセージ（AI不使用時）
# =====================================================================
def generate_base_first_message(user_name, look_type):
    if "ギャル" in look_type or "グラドル" in look_type:
        return f"「はじめましてー！マッチありがとう✨ {user_name}さんって普段どのへんで飲むことが多いですかー？」"
    return f"「はじめまして！マッチできて嬉しいです✨ {user_name}さんは普段どのへんで遊ぶことが多いんですか？」"

def generate_base_third_message(user_name, char_type, job):
    if "愛され" in char_type or "マシュマロ" in char_type:
        return f"「え〜！そんな美味しいお店あるんですか？今度絶対そこに連れていってくださいねっ！おねだりです、約束ですよ？あ、大変！先輩に呼ばれちゃいました💦 またすぐお話ししてくださいね！」"
    return f"「あ、いいですね！焼き鳥とかめっちゃ好きです。\nあ、やばい、今からミーティングだったの忘れてた💦 ちょっと行ってきます！\n仕事だるいしサボっちゃいたいなー。{user_name}さんは今日仕事サボったりしてないですか？」"

# =====================================================================
# 4. 【AI文章生成層】GrokのAPIを呼び出す
# =====================================================================
def ask_grok_ai(prompt):
    time.sleep(1.5)
    # ★ ここが安全な「鍵穴」に変わりました！GitHubに上げても安全です。
    api_key = st.secrets["XAI_API_KEY"]
    
    url = "https://api.x.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    safe_prompt = prompt.encode('utf-8', errors='ignore').decode('utf-8')
    payload = {
        "model": "grok-4.3",
        "messages": [{"role": "user", "content": safe_prompt}],
        "temperature": 0.7,
        "max_tokens": 120  # 少し柔軟性を持たせるために120に微増
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
st.set_page_config(page_title="AIキャスト 職業連動プロ版", layout="centered")

st.title("🤖 小嶋企画 AIチャットエンジン (職業連動プロ版)")
st.write("女性の職業に最もマッチした最新ニュースをAIが自動選別して1通目を生成します。")

user_name = st.text_input("相手のユーザー名", "小嶋")

if st.button("▶︎ AIチャットを生成する", type="primary"):
    casts = load_cast_master_from_excel()
    if not casts:
        st.stop()
        
    # 最新ニュースの箇条書きを取得
    news_list_text = get_multiple_trending_news()

    with st.spinner("AIが職業とニュースの相性を分析してセリフを生成中..."):
        for cast in casts[:4]:  
            st.subheader(f"👩‍🦰 {cast['name']} ({cast['age']}歳 / {cast['job']} / {cast['look_type']})")
            
            # ------------------ 1通目の処理（職業×ニュース自動連動） ------------------
            dice_1st = random.randint(1, 100)
            if dice_1st <= 20:
                # 命令文を「職業に合うニュースを自分で選べ」に超絶パワーアップ
                prompt_1st = (
                    f"あなたはマッチングアプリにいる実在の女の子「{cast['name']}（{cast['age']}歳・職業:{cast['job']}・性格:{cast['char_type']}）」です。\n"
                    f"相手の男（{user_name}さん）へのフランクな最初のメッセージを1通だけ書いてください。\n\n"
                    f"【最重要ルール】：\n"
                    f"以下の最新ニュースのリストから、あなたの「職業」や「年齢」に最も関わりが深く、会話として出しても不自然じゃない話題を『1つだけ』あなたの意思で選んで、チャットの中に自然に混ぜてください。\n"
                    f"例えば、IT系なら経済や技術系、大学生ならエンタメやトレンド、といったように親和性の高いものを結びつけてください。\n\n"
                    f"【最新ニュースリスト】:\n{news_list_text}\n\n"
                    f"【絶対禁止】：サクラっぽくなるので「笑」や「（笑）」は一切使わないでください。短文でメッセージ本文のみをスマートに出力してください。"
                )
                message_1st = ask_grok_ai(prompt_1st)
                if not message_1st:
                    message_1st = generate_base_first_message(user_name, cast['look_type'])
            else:
                message_1st = generate_base_first_message(user_name, cast['look_