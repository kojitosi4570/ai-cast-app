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

    # 👑 【スリムグラデーション仕様・一体型フォトスライダー】
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
    
    # 写真スライダーを画面に埋め込み
    components.html(slider_html, height=490, scrolling=False)
    
    # 👑 【おじさん熱狂仕様】：隙間を詰めて、写真の下フチに「半分重なる（ネガティブマージン：margin-top -45px）」で丸ボタンを完全に上書き配置
    st.write(" ")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("✕", key="skip_btn", use_container_width=True):
            # 🛡️ 解決：クエリパラメータから action キーを安全に削除してリロードすることで、クラッシュを永久に防止
            if "action" in st.query_params:
                del st.query_params["action"]
            st.session_state.swipe_index += 1
            st.rerun()
    with col_b2:
        if st.button("❤️", key="like_btn", use_container_width=True):
            add_match(USER_ID, c_id)
            st.session_state.last_matched_cast = active_cast
            if "action" in st.query_params:
                del st.query_params["action"]
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
            5. 会話を一方的に受け止めて終わらせるのではない、返答の最後には、必ず相手に「〇〇さんはどうですか？😊」や「普段はどのへんで観てるんですか？♪」といった【自然な質問や問いかけ】を1つ入れて、相手が返信しやすいフックを作ってください。
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