import streamlit as st
# ページ設定（必ずファイルの先頭）
st.set_page_config(page_title="赤枠点滅 APNG Generator", layout="centered")

from PIL import Image, ImageDraw
import io

# --- 設定値 ---
TARGET_WIDTH = 600
TARGET_HEIGHT = 400
BORDER_COLOR = (255, 0, 0, 255) # 赤色 (不透明)
BORDER_WIDTH = 20               # 枠の太さ
MAX_FILE_SIZE_KB = 300

# 5フレーム(1秒) / 2ループ / 5fps
FIXED_TOTAL_FRAMES = 5
FIXED_LOOP_COUNT = 2
FRAME_DURATION = 200 # 0.2秒

def process_image(uploaded_file):
    # 1. 画像の読み込みとキャンバス作成
    original_img = Image.open(uploaded_file).convert("RGBA")
    
    # 600x400のベース作成（背景は白にしておくと広告として綺麗です）
    base_img = Image.new("RGBA", (TARGET_WIDTH, TARGET_HEIGHT), (255, 255, 255, 255))
    
    # 元画像をリサイズして中央配置（アスペクト比維持）
    # 枠線で隠れないように少しだけ内側に縮小しても良いですが、
    # ここでは仕様通り600x400いっぱいに配置して上から枠を描画します。
    original_img.thumbnail((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)
    x = (TARGET_WIDTH - original_img.width) // 2
    y = (TARGET_HEIGHT - original_img.height) // 2
    base_img.paste(original_img, (x, y), original_img)
    
    # 2. フレーム素材の作成
    
    # 【ON画像】 赤枠あり
    frame_on = base_img.copy()
    draw = ImageDraw.Draw(frame_on)
    # 枠線を描画（内側に向かって太くなるように計算）
    # rectangleのwidth指定は中心から太くなるため、座標を少し調整して内側に収める工夫もできますが、
    # シンプルに太く描画します。
    draw.rectangle(
        [(0, 0), (TARGET_WIDTH - 1, TARGET_HEIGHT - 1)],
        outline=BORDER_COLOR,
        width=BORDER_WIDTH
    )

    # 【OFF画像】 赤枠なし（ベース画像そのまま）
    frame_off = base_img.copy()
    
    # 3. アニメーションシーケンス作成 (5フレーム)
    # パターン: ON -> OFF -> ON -> OFF -> ON
    frames = []
    for i in range(FIXED_TOTAL_FRAMES):
        if i % 2 == 0:
            frames.append(frame_on)
        else:
            frames.append(frame_off)
            
    # 4. 保存処理 (フルカラー維持・無圧縮)
    output_io = io.BytesIO()
    frames[0].save(
        output_io,
        format="PNG",
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION,
        loop=FIXED_LOOP_COUNT,
        optimize=True
    )
    
    data = output_io.getvalue()
    size_kb = len(data) / 1024
    
    return data, size_kb

# --- UI表示 ---

st.title("🟥 赤枠点滅 APNG生成")
st.markdown("""
画像をアップロードすると、**太い赤枠が点滅するアニメーション**を自動生成します。
* **仕様**: 600x400px / 5フレーム / 2ループ
* **画質**: フルカラー（劣化なし）
""")

uploaded_file = st.file_uploader("画像をアップロード (JPG/PNG)", type=["jpg", "png"])

if uploaded_file:
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.caption("元画像")
        st.image(uploaded_file, use_column_width=True)

    # 自動実行
    with st.spinner("生成中..."):
        apng_data, size_kb = process_image(uploaded_file)
    
    with col2:
        st.caption("生成結果 (プレビュー)")
        st.image(apng_data, use_column_width=True)
        
        # 容量判定
        if size_kb <= MAX_FILE_SIZE_KB:
            st.success(f"✅ 容量: {size_kb:.1f} KB (OK)")
        else:
            st.error(f"⚠️ 容量: {size_kb:.1f} KB (規定超過)")
            st.caption("※フルカラー維持のため圧縮していません。")
            
        st.download_button(
            label="ダウンロード",
            data=apng_data,
            file_name="red_frame_blink.png",
            mime="image/png",
            type="primary"
        )
