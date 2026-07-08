# ============================================================
# 💓 【Tapple風 大改善版】お相手探しスワイプ画面
# ============================================================
if st.session_state.current_tab == "🔍 お相手探し":
    st.markdown("### 🔍 好みのAIキャストを見つけよう！")

    # （お好み検索は省略可）
    with st.expander("⚙️ お好み詳細検索"):
        filter_age = st.slider("年齢層の選択", 18, 45, (18, 35))

    filtered_casts = [c for c in casts if filter_age[0] <= c["age"] <= filter_age[1]]
    
    if not filtered_casts:
        st.info("条件に合うお相手が見つかりません。")
        st.stop()

    if st.session_state.swipe_index >= len(filtered_casts):
        st.session_state.swipe_index = 0

    active_cast = filtered_casts[st.session_state.swipe_index]
    c_id = active_cast["id"]

    # 画像パス取得
    photo_paths = [
        os.path.join(IMAGE_DIR, c_id, f"{c_id}_photo_1_main.png"),
        os.path.join(IMAGE_DIR, c_id, f"{c_id}_photo_2_sub.png"),
        os.path.join(IMAGE_DIR, c_id, f"{c_id}_photo_3_sub.png"),
        os.path.join(IMAGE_DIR, c_id, f"{c_id}_photo_4_sub.png"),
        os.path.join(IMAGE_DIR, c_id, f"{c_id}_photo_5_sub.png"),
    ]
    img_srcs = [get_image_base64(p) or "https://placehold.co/400x500?text=No+Image" for p in photo_paths]

    # ==================== Tapple風カード（大幅改善版） ====================
    slider_html = f"""
    <style>
        .tapple-wrapper {{
            position: relative;
            width: 100%;
            max-width: 420px;
            margin: 0 auto;
            border-radius: 24px;
            overflow: hidden;
            box-shadow: 0 12px 32px rgba(0,0,0,0.18);
            background: #000;
            aspect-ratio: 9 / 14;
        }}
        .photo-track {{
            width: 100%;
            height: 100%;
            display: flex;
            transition: transform 0.3s ease-out;
        }}
        .photo-track img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            flex-shrink: 0;
        }}
        .info-overlay {{
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            background: linear-gradient(transparent, rgba(0,0,0,0.88));
            color: white;
            padding: 22px 16px 16px;
            z-index: 10;
        }}
        .name-age {{
            font-size: 26px;
            font-weight: 700;
            margin-bottom: 2px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.6);
        }}
        .job-tag {{
            font-size: 14px;
            opacity: 0.95;
        }}
    </style>

    <div class="tapple-wrapper">
        <!-- 写真スライダー -->
        <div class="photo-track" id="track">
            {"".join([f'<img src="{src}">' for src in img_srcs])}
        </div>

        <!-- 情報オーバーレイ -->
        <div class="info-overlay">
            <div class="name-age">{active_cast['name']} ({active_cast['age']}歳)</div>
            <div class="job-tag">💼 {active_cast['job']} ・ 📍 元住吉周辺</div>
        </div>
    </div>

    <script>
        let idx = 0;
        const track = document.getElementById('track');
        function update() {{
            track.style.transform = `translateX(${{-idx * 100}}%)`;
        }}
        function nextSlide() {{ if (idx < 4) {{ idx++; update(); }} }}
        function prevSlide() {{ if (idx > 0) {{ idx--; update(); }} }}
    </script>
    """

    components.html(slider_html, height=530, scrolling=False)

    # ==================== いいね × ボタン（写真のすぐ下に配置） ====================
    st.write("")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("✕", key="skip_btn", use_container_width=True):
            st.session_state.swipe_index += 1
            st.rerun()
    
    with col2:
        if st.button("❤️", key="like_btn", use_container_width=True):
            add_match(USER_ID, c_id)
            st.session_state.last_matched_cast = active_cast
            st.rerun()

    # プロフィール詳細（アコーディオンで隠す）
    with st.expander(f"📝 {active_cast['name']}ちゃんの自己紹介を詳しく見る"):
        st.markdown(active_cast['profile_text'])