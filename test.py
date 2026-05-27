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
    
    if not news_candidates:
        news_candidates = [
            "大谷選手がまた特大ホームランを放ち驚異的な記録を更新中",
            "日本の主要株価が急変動、経済ニュースで投資家の注目集まる",
            "最新のAI技術を搭載したスマホアプリが世界中でトレンドに",
            "今年の最新トレンドファッションや注目ブランドが発表"
        ]
    
    return "\n".join([f"- {title}" for title in news_candidates[:8]])

# =====================================================================
# 3. 【ロジック層】定型文メッセージ（AI不使用時・すべて質問締めに改造）
# =====================================================================
def generate_base_first_message(user_name, look_type):
    if "ギャル" in look_type or "グラドル" in look_type:
        return f"「はじめましてー！マッチありがとう✨ {user_name}さんって普段どのへんで飲むことが多いですかー？」"
    return f"「はじめまして！マッチできて嬉しいです✨ {user_name}さんは普段どのへんで遊ぶことが多いんですか？」"

def generate_base_second_message(user_name, char_type):
    if "甘え" in char_type or "愛され" in char_type:
        return f"「{user_name}さん、今日もお仕事本当にお疲れ様ですっ🥺✨ 毎日がんばってて偉すぎます…！無理しすぎないで、たまには私に甘えてくださいね？{user_name}さんは今日、美味しいもの食べられましたか？」"
    return f"「お仕事お疲れ様です！日々バタバタだと突っ走りたくなっちゃうけど、たまには息抜きも必要ですよ。{user_name}さんがホッとできるようなお喋りができたら嬉しいです。最近、ちゃんと夜眠れてますか？」"

def generate_base_third_message(user_name, char_type, job):
    if "愛され" in char_type or "マシュマロ" in char_type:
        return f"「え〜！そんな美味しいお店あるんですか？今度絶対そこに連れていってくださいねっ！約束ですよ？あ、大変！先輩に呼ばれちゃいました💦 またすぐお話ししてくれますか？」"
    return f"「あ、いいですね！焼き鳥とかめっちゃ好きです。\nあ、やばい、今からミーティングだったの忘れてた💦 ちょっと行ってきます！\n仕事だるいしサボっちゃいたいなー。{user_name}さんは今日仕事サボったりしてないですか？」"

# =====================================================================
# 4. 【AI文章生成層】GrokのAPIを呼び出す（安全のための1.5秒ブレーキ入り）
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
st.set_page_config(page_title="AIキャスト 職業連動プロ版", layout="centered")

st.title("🤖 小嶋企画 AIチャットエンジン (職業連動プロ版)")
st.write("女性の職業に最もマッチした最新ニュースをAIが自動選別して1通目を生成します。")

user_name = st.text_input("相手のユーザー名", "小嶋")

if st.button("▶︎ AIチャットを生成する", type="primary"):
    casts = load_cast_master_from_excel()
    if not casts:
        st.stop()
        
    news_list_text = get_multiple_trending_news()

    for cast in casts[:4]:  
        st.subheader(f"👩‍🦰 {cast['name']} ({cast['age']}歳 / {cast['job']} / {cast['look_type']})")
        
        # ------------------ 1通目の処理（ニュース確率 50% / 質問締め強化） ------------------
        dice_1st = random.randint(1, 100)
        if dice_1st <= 50:
            prompt_1st = (
                f"あなたはマッチングアプリにいる実在の女の子「{cast['name']}（{cast['age']}歳・職業:{cast['job']}・性格:{cast['char_type']}）」です。\n"
                f"相手の男（{user_name}さん）へのフランクな最初のメッセージを1通だけ書いてください。\n\n"
                f"【最重要ルール】：\n"
                f"1. 以下の最新ニュースのリストから、あなたの「職業」や「年齢」に最も関わりが深い話題を『1つだけ』選んで、自然に混ぜてください。\n"
                f"【最新ニュースリスト】:\n{news_list_text}\n"
                f"2. 【質問必須】：メッセージの最後は、そのニュースに関連した、相手が1秒で返信できるフランクな「質問（〜ですか？など）」で必ず締めくくってください。\n\n"
                f"【絶対禁止】：サクラっぽくなるので「笑」や「（笑）」は一切使わないでください。短文で本文のみを出力。"
            )
            message_1st = ask_grok_ai(prompt_1st)
            if not message_1st:
                message_1st = generate_base_first_message(user_name, cast['look_type'])
        else:
            message_1st = generate_base_first_message(user_name, cast['look_type'])
            
        st.info(f"**【1通目】**\n{message_1st}")
        
        # ------------------ 2通目の処理（メンタルケア / 質問締め強化） ------------------
        prompt_2nd = (
            f"あなたはマッチングアプリの女の子「{cast['name']}（{cast['age']}歳・職業:{cast['job']}・性格:{cast['char_type']}）」です。\n"
            f"相手の男（{user_name}さん）への『2通目』のチャットを書いてください。\n\n"
            f"【目的】：男が一番求めている、メンタルを包み込むような最高の癒やしを提供します。\n"
            f"【内容】：相手の日常や仕事の疲れを完璧に肯定し、共感し、「がんばってて偉い、尊敬しちゃう」というニュアンスを、あなたのキャラクター（{cast['char_type']}）全開の口調で最高に気持ちいい文章にしてください。\n"
            f"【質問必須】：メッセージの最後は、相手の体調を気遣うような、1秒で返せるフランクな「質問（最近ちゃんと寝られてる？、今日美味しいもの食べた？など）」で必ず締めくくってください。\n\n"
            f"【絶対禁止】：「笑」や「（笑）」は絶対禁止。短文で本文のみを出力。"
        )
        message_2nd = ask_grok_ai(prompt_2nd)
        if not message_2nd:
            message_2nd = generate_base_second_message(user_name, cast['char_type'])
            
        st.warning(f"**【2通目（メンタルケア）】**\n{message_2nd}")
        
        # ------------------ 3通目の処理（ストイックギャップ / 質問締め強化） ------------------
        dice_3rd = random.randint(1, 100)
        if dice_3rd <= 8:
            prompt_3rd = (
                f"あなたはマッチングアプリの女の子「{cast['name']}（{cast['age']}歳・職業:{cast['job']}・見た目:{cast['look_type']}）」です。\n"
                f"相手の男（{user_name}さん）への3通目のチャットを書いてください。\n\n"
                f"【条件】：普段は男に媚びていますが、実は自分の仕事（{cast['job']}）には超ストイックで真剣です。周りから怖いと言われるくらい集中しちゃうギャップを、絵文字なしの凛とした真面目なトーンで伝えてください。\n"
                f"【質問必須】：メッセージの最後は、仕事に関する、相手が答えやすいフランクな「質問（{user_name}さんは仕事中集中すると周り見えなくなるタイプ？など）」で必ず締めくくってください。\n\n"
                f"【絶対禁止】：「笑」や「（笑）」は絶対禁止。短文で本文のみを出力。"
            )
            message_3rd = ask_grok_ai(prompt_3rd)
            if not message_3rd:
                message_3rd = generate_base_third_message(user_name, cast['char_type'], cast['job'])
        else:
            message_3rd = generate_base_third_message(user_name, cast['char_type'], cast['job'])
            
        st.success(f"**【3通目】**\n{message_3rd}")
        st.divider() 
            
    st.balloons()
