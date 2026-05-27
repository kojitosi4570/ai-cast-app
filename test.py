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
        
        # 「市名 ＋ 駅名」のシンプル表記
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
st.set_page_config(page_title="小嶋企画 AIキャスト魂連動版", layout="centered")

st.title("🤖 小嶋企画 AIチャットエンジン")

user_name = st.text_input("相手のユーザー名", "小嶋")

if st.button("▶︎ AIチャットを生成する", type="primary"):
    casts = load_cast_master_from_excel()
    if not casts:
        st.stop()
        
    news_list_text = get_multiple_trending_news()

    for cast in casts[:30]:  
        st.subheader(f"👩‍🦰 {cast['name']} ({cast['age']}歳 / {cast['job']} / {cast['look_type']} / 📍最寄り:{cast['station']})")
        
        # 👑 【コア設定】キャラクタータイプをAIに深く魂まで叩き込む仕込み
        char_instruction = (
            f"【あなたの固有キャラクター性格】：あなたの性格・言動スタイルは「{cast['char_type']}」です。\n"
            f"ただのタメ口ではなく、この性格の特徴（例：『王道・愛され系』なら甘え上手で人懐っこい口調、『そっけない・塩対応系』ならぶっきらぼうで冷めたクールな口調、『マシュマロ』なら全肯定して包み込むお姉さん口調）を、言葉遣いや語尾、文章のテンポに【極限まで強く反映】させて七変化させてください。全員一律のありきたりな文章は厳禁です。"
        )
        
        # ------------------ 1通目の処理 ------------------
        dice_1st = random.randint(1, 100)
        if dice_1st <= 50:
            prompt_1st = (
                f"あなたはマッチングアプリにいる実在の女の子「{cast['name']}（{cast['age']}歳・職業:{cast['job']}）」です。\n"
                f"{char_instruction}\n"
                f"相手の男（{user_name}さん）への最初のフランクなメッセージを1通だけ書いてください。\n\n"
                f"【最重要ルール】：\n"
                f"1. 以下の最新ニュースのリストから話題を『1つだけ』選んで、自然に混ぜてください。\n"
                f"【最新ニュースリスト】:\n{news_list_text}\n"
                f"2. 【質問必須】：最後はニュースに関連した、相手が1秒で返せるフランクな質問で締めてください。\n"
                f"【絶対禁止】：「笑」「（笑）」「爆笑」や笑う絵文字（🤣😅等）は滑るため【一切使用禁止】。真顔でスマートに出力。"
            )
            message_1st = ask_grok_ai(prompt_1st)
            if not message_1st:
                message_1st = generate_base_first_message(user_name, cast['look_type'])
        else:
            message_1st = generate_base_first_message(user_name, cast['look_type'])
            
        st.info(f"**【1通目】**\n{message_1st}")
        
        # ------------------ 2通目の処理（4変化 ➔ キャラクター連動超強化） ------------------
        dice_2nd = random.randint(1, 100)
        
        base_prompt_2nd = (
            f"あなたはマッチングアプリの女の子「{cast['name']}（{cast['age']}歳・職業:{cast['job']}）」です。\n"
            f"{char_instruction}\n"
            f"相手の男（{user_name}さん）への『2通目』のチャットを書いてください。\n\n"
            f"【最重要・不快ワードの絶対禁止】：男を呼ぶときは必ず「{user_name}さん」か「{user_name}くん」です。「お前」「貴様」「あなた」「あんた」および「呼び捨て」は【絶対に禁止】とします。\n"
            f"【最重要禁止ルール】：胸、おっぱい、爆乳など直接的なエロ単語は審査落ち防止のため【一切禁止】とします。\n"
            f"【最重要・（笑）の完全禁止】：「笑」「（笑）」や笑う絵文字は【一切使用禁止】。あえて真顔でサラッと言い放つ空気感にしてください。\n"
            f"【質問必須】：最後は日常を気遣う簡単な質問で締めてください。\n"
            f"【出力形式】：2〜3行の短いメッセージ本文のみを出力。\n\n"
        )
        
        if dice_2nd <= 20:
            prompt_2nd = base_prompt_2nd + (
                "【個別ミッション：王道の純粋癒やし（敬語）】\n"
                "あなたのキャラクターの個性を保ったまま、敬語・丁寧語を崩さずに、優しくクリーンな精神的ケアを提供してください。\n"
                "「本当にお疲れ様です」と男を最高に気持ちよくさせて油断させる文面にしてください。"
            )
        elif dice_2nd <= 50:
            prompt_2nd = base_prompt_2nd + (
                "【個別ミッション：王道の純粋癒やし（ガチタメ口）】\n"
                "あなたのキャラクターの個性を全開にしたフランクなタメ口にしてください。\n"
                "「今日もお疲れ様！いつもがんばってて偉いよ」というニュアンスを、あなたの性格に完璧に染め上げて脳をバグらせてください。"
            )
        elif dice_2nd <= 80:
            prompt_2nd = base_prompt_2nd + (
                "【個別ミッション：おちゃめな匂わせ短文（ガチタメ口・パワーワード自動生成）】\n"
                "あなたのキャラクターの個性を全開にしたフランクなタメ口にしてください。\n"
                "男が勝手にフィジカルな想像（密着感や柔らかさ）をして突っ込んでしまうような『お茶目なオリジナルパワーワード（例え話）』をあなたがその場で新しく1つ生み出して混ぜてください。\n"
                "※家具、寝具、スイーツなどの「柔らかいモノ」を人間と掛け合わせること（例：歩くマシュマロソファ、全自動ヨシヨシ毛布など）。エロ単語は絶対禁止ですが、あなたのキャラクターの口調で真顔で放ってください。"
            )
        else:
            prompt_2nd = base_prompt_2nd + (
                "【個別ミッション：強烈ボケ（ガチタメ口）】\n"
                "あなたのキャラクターの個性を全開にしたフランクなタメ口にしてください。\n"
                "男が思わずツッコミを入れたくなる短いボケ（インパクト抜群の男勝りなワードや、ゲルゲロパーレー等の異次元な造語ボケ）を、あなたのキャラクターが真顔で言い放つトーンで出力してください。"
            )
            
        message_2nd = ask_grok_ai(prompt_2nd)
        if not message_2nd:
            message_2nd = generate_base_second_message(user_name, cast['char_type'])
            
        st.warning(f"**【2通目（メンタルケア）】**\n{message_2nd}")
        
        # ------------------ 3通目の処理（★確率30%へ引き上げ ＆ キャラ連動） ------------------
        dice_3rd = random.randint(1, 100)
        if dice_3rd <= 30: # ★ 8% ➔ 30% に超大幅強化！
            prompt_3rd = (
                f"あなたはマッチングアプリの女の子「{cast['name']}（{cast['age']}歳・職業:{cast['job']}）」です。\n"
                f"【重要ミッション：ストイックギャップ】\n"
                f"普段は男に媚びたりキャラクター（{cast['char_type']}）を演じていますが、実は自分の本職（{cast['job']}）には超ストイックで真剣です。周りから怖いと言われるくらい職人として集中しちゃうプロとしてのギャップを、絵文字を一切排除した、凛とした真面目なトーンで伝えて男をドキッとさせてください。\n"
                f"【質問必須】：メッセージの最後は、仕事に関する、相手が答えやすいフランクな質問（〇〇さんは仕事中集中すると周り見えなくなるタイプ？など）で必ず締めくくってください。\n\n"
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
