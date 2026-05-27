import streamlit as st
import random
import os
import time  
import pandas as pd
import xml.etree.ElementTree as ET
import requests

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
            "川崎市武蔵小杉駅",
            "川崎市鹿島田駅",
            "川崎市元住吉駅",
            "川崎市溝の口駅",
            "川崎市川崎駅",
            "横浜市日吉駅",
            "横浜市綱島駅",
            "横浜市菊名駅",
            "横浜市新横浜駅",
            "さいたま市大宮駅",
            "川越市川越駅"
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
        st.error(f"⚠️ Excelファイルの読み込み中にエラーが発生しました: {e}")
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
        news_candidates = [
            "大谷選手がまた特大ホームランを放ち驚異的な記録を更新中",
            "日本の主要株価が急変動、経済ニュースで投資家の注目集まる",
            "最新のAI技術を搭載したスマホアプリが世界中でトレンドに",
            "今年の最新トレンドファッションや注目ブランドが発表"
        ]
    
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
    if "愛され" in char_type or "マシュマロ" in char_type:
        return f"「え〜！そんな美味しいお店あるんですか？今度絶対そこに連れていってくださいねっ！約束ですよ？あ、大変！先輩に呼ばれちゃいました💦 またすぐお話ししてくれますか？」"
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
st.set_page_config(page_title="AIキャスト 極悪自動生成プロ版", layout="centered")

st.title("🤖 小嶋企画 AIチャットエンジン")

user_name = st.text_input("相手のユーザー名", "小嶋")

if st.button("▶︎ AIチャットを生成する", type="primary"):
    casts = load_cast_master_from_excel()
    if not casts:
        st.stop()
        
    news_list_text = get_multiple_trending_news()

    for cast in casts[:30]:  
        st.subheader(f"👩‍🦰 {cast['name']} ({cast['age']}歳 / {cast['job']} / {cast['look_type']} / 📍最寄り:{cast['station']})")
        
        # ------------------ 1通目の処理 ------------------
        dice_1st = random.randint(1, 100)
        if dice_1st <= 50:
            prompt_1st = (
                f"あなたはマッチングアプリにいる実在の女の子「{cast['name']}（{cast['age']}歳・職業:{cast['job']}・性格:{cast['char_type']}）」です。\n"
                f"相手の男（{user_name}さん）へのフランクな最初のメッセージを1通だけ書いてください。\n\n"
                f"【最重要ルール】：\n"
                f"1. 以下の最新ニュースのリストから、あなたの「職業」や「年齢」に最も関わりが深い話題を『1つだけ』選んで、自然に混ぜてください。\n"
                f"【最新ニュースリスト】:\n{news_list_text}\n"
                f"2. 【質問必須】：メッセージの最後は、そのニュースに関連した、相手が1秒で返信できるフランクな「質問（〜ですか？など）」で必ず締めくくってください。\n\n"
                f"【絶対禁止】：「笑」「（笑）」「爆笑」や、照れ隠しの笑う絵文字（🤣😂😆😅😁など）は滑っている感が出て男が萎えるため【一切使用禁止】とします。真顔でスマートに出力してください。"
            )
            message_1st = ask_grok_ai(prompt_1st)
            if not message_1st:
                message_1st = generate_base_first_message(user_name, cast['look_type'])
        else:
            message_1st = generate_base_first_message(user_name, cast['look_type'])
            
        st.info(f"**【1通目】**\n{message_1st}")
        
        # ------------------ 2通目の処理 ------------------
        dice_2nd = random.randint(1, 100)
        
        base_prompt_2nd = (
            f"あなたはマッチングアプリの女の子「{cast['name']}（{cast['age']}歳・職業:{cast['job']}・性格:{cast['char_type']}）」です。\n"
            f"相手の男（{user_name}さん）への『2通目』のチャットを書いてください。\n\n"
            f"【最重要・不快ワードの絶対禁止】：相手の男（{user_name}さん）を呼ぶときは、必ず「{user_name}さん」や「{user_name}くん」と呼んでください。「お前」「貴様」「あなた」「あんた」という呼び方、および名前の「呼び捨て」は、距離感を冷めさせたり相手を不快にさせるため【絶対に禁止】とします。口が裂けてもこれら禁止ワードは出力しないでください。\n"
            f"【最重要禁止ルール】：胸、おっぱい、爆乳、お尻、バスト、胸部といった『直接的なエロ・身体パーツ単語』は決済審査落ちを避けるため、使用を【一切禁止】とします。\n"
            f"【最重要・（笑）の完全禁止】：「笑」「（笑）」「爆笑」や、笑う絵文字（🤣😂😆😅など）は滑っている感が出るため【一切使用禁止】です。あえて真顔でサラッと言い放つ空気感にしてください。\n"
            f"【質問必須】：最後は、相手の日常を気遣う、1秒で返せる簡単な質問で必ず締めくくってください。\n"
            f"【出力形式】：2〜3行の短いメッセージ本文のみを出力してください。\n\n"
        )
        
        if dice_2nd <= 20:
            # ① 王道の純粋癒やし・敬語ver（20%）
            prompt_2nd = base_prompt_2nd + (
                "【個別ミッション：王道の純粋癒やし（敬語）】\n"
                "敬語・丁寧語を崩さずに、優しくクリーンな精神的ケアを提供してください。\n"
                "「本当にお疲れ様です、がんばってて凄いです」と、男を最高に気持ちよくさせて油断させる丁寧な文面にしてください。"
            )
        elif dice_2nd <= 50:
            # ② 王道の純粋癒やし・タメ口ver（30%）
            prompt_2nd = base_prompt_2nd + (
                "【個別ミッション：王道の純粋癒やし（ガチタメ口）】\n"
                "敬語を完全に捨てて、フランクなタメ口にしてください。\n"
                "「{user_name}くん今日もお疲れ様！いつもがんばってて本当に偉いよ。無理しすぎないでね」という風に、優しく包み込むようなタメ口で男の脳をバグらせてください。※『お前』や『あなた』、呼び捨て等は絶対禁止です。"
            )
        elif dice_2nd <= 80:
            # ③ おちゃめな匂わせ・タメ口（ワード無限生成ver）（30%）
            prompt_2nd = base_prompt_2nd + (
                "【個別ミッション：おちゃめな匂わせ短文（ガチタメ口・パワーワード自動生成）】\n"
                "敬語を完全に捨てて、フランクなタメ口にしてください。\n"
                "男が勝手にフィジカルな想像（密着感や柔らかさ、癒やし）をして突っ込んでしまうような『お茶目なオリジナルパワーワード（例え話）』をあなたがその場で新しく1つ生み出して混ぜてください。\n"
                "※コツ：家具、寝具、スイーツなどの「柔らかいモノ」「温かいモノ」に人間を掛け合わせること（例：歩くマシュマロソファ、全自動ヨシヨシ機など）。\n"
                "※直接的なエロ単語（胸、お尻など）は絶対禁止ですが、男がギリギリ妄想してしまうユーモアを真顔で放ってください。\n"
                "※『お前』や『あなた』、呼び捨て等は絶対禁止です。"
            )
        else:
            # ④ ツッコミ待ち大ボケ ＆ 異次元ボケ・タメ口ver（20%）
            prompt_2nd = base_prompt_2nd + (
                "【個別ミッション：強烈ボケ（ガチタメ口）】\n"
                "敬語を完全に捨てて、フランクなタメ口にしてください。\n"
                "確率に応じて以下のいずれかの方向性で、男が思わずツッコミを入れたくなる短いタメ口を真顔で作ってください。\n"
                "パターンA：「半端ねぇマウンテン級の癒やしパワー」「たまんねぇ癒やし」「やべぇ」といった、男勝りでインパクト抜群のタメ口ワード。\n"
                "パターンB：「ゲルゲロパーレー」など意味不明な新しい造語を作り、「私の〇〇で吹き飛ばしてあげる」という電波系のタメ口ボケ。\n"
                "※『お前』『あなた』、呼び捨て等は絶対禁止です。"
            )
            
        message_2nd = ask_grok_ai(prompt_2nd)
        if not message_2nd:
            message_2nd = generate_base_second_message(user_name, cast['char_type'])
            
        st.warning(f"**【2通目（メンタルケア）】**\n{message_2nd}")
        
        # ------------------ 3通目の処理 ------------------
        dice_3rd = random.randint(1, 100)
        if dice_3rd <= 8:
            prompt_3rd = (
                f"あなたはマッチングアプリの女の子「{cast['name']}（{cast['age']}歳・職業:{cast['job']}・見た目:{cast['look_type']}）」です。\n"
                f"相手の男（{user_name}さん）への3通目のチャットを書いてください。\n\n"
                f"【条件】：普段は男に媚びていますが、実は自分の仕事（{cast['job']}）には超ストイックで真剣です。周りから怖いと言われるくらい集中しちゃうギャップを、絵文字なしの凛とした真面目なトーンで伝えてください。\n"
                f"【質問必須】：メッセージの最後は、仕事に関する、相手が答えやすいフランクな「質問（{user_name}さんは仕事中集中すると周り見えなくなるタイプ？など）」で必ず締めくくってください。\n\n"
                f"【絶対禁止】：「笑」「（笑）」は絶対禁止。短文で本文のみを出力。"
            )
            message_3rd = ask_grok_ai(prompt_3rd)
            if not message_3rd:
                message_3rd = generate_base_third_message(user_name, cast['char_type'], cast['job'])
        else:
            message_3rd = generate_base_third_message(user_name, cast['char_type'], cast['job'])
            
        st.success(f"**【3通目】**\n{message_3rd}")
        st.divider() 
            
    st.balloons()
