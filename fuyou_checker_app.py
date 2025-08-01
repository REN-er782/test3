
import streamlit as st

st.set_page_config(page_title="扶養控除 判定フロー", layout="centered")
st.title("扶養控除 判定ツール（配偶者・親族対応）")

st.markdown("---")

対象区分 = st.radio("対象者は誰ですか？", ["配偶者", "配偶者以外の親族・子"])

if 対象区分 == "配偶者":
    年収本人 = st.radio("納税者本人の年収は1,000万円以上ですか？", ["はい", "いいえ"])

    if 年収本人 == "はい":
        st.markdown("#### 控除対象外の可能性あり")
        収入 = st.slider("配偶者の年収（万円）", 0, 300, 130)
        if 収入 <= 130:
            st.write("控除 × ／ 健保 ○ ／ 手当 ○")
        elif 130 < 収入 <= 160:
            st.write("控除 × ／ 健保 × ／ 手当 ○")
        else:
            st.write("控除 × ／ 健保 × ／ 手当 ×")

    else:
        収入 = st.slider("配偶者の年収（万円）", 0, 300, 130)
        if 収入 <= 123:
            st.write("配偶者控除 ○ ／ 健保 ○ ／ 手当 ○")
        elif 123 < 収入 <= 130:
            st.write("配偶者特別控除 ○ ／ 健保 ○ ／ 手当 ○")
        elif 130 < 収入 <= 160:
            st.write("配偶者特別控除 ○ ／ 健保 × ／ 手当 ○")
        elif 160 < 収入 <= 201:
            st.write("配偶者特別控除（段階）○ ／ 健保 × ／ 手当 ×")
        else:
            st.write("配偶者特別控除（段階）○ ／ 健保 × ／ 手当 ×")

else:
    年齢 = st.slider("対象者の年齢", 0, 100, 20)

    if 年齢 <= 16:
        st.write("控除 ×（※住民税は控除 ○）／ 健保 ○ ／ 手当 ○")
    elif 19 <= 年齢 <= 22:
        収入 = st.slider("対象者の年収（万円）", 0, 300, 100)
        if 収入 <= 150:
            st.write("控除 ○ ／ 健保 ○ ／ 手当 ○")
        elif 150 < 収入 <= 160:
            st.write("控除 ○ ／ 健保 × ／ 手当 ○")
        elif 160 < 収入 <= 188:
            st.write("控除（段階）○ ／ 健保 × ／ 手当 ×")
        else:
            st.write("控除 × ／ 健保 × ／ 手当 ×")
    else:
        収入 = st.slider("対象者の年収（万円）", 0, 300, 100)
        if 収入 <= 123:
            st.write("控除 ○ ／ 健保 ○ ／ 手当 ○")
        elif 123 < 収入 <= 130:
            st.write("控除 × ／ 健保 ○ ／ 手当 ○")
        elif 130 < 収入 <= 160:
            st.write("控除 × ／ 健保 × ／ 手当 ○")
        else:
            st.write("控除 × ／ 健保 × ／ 手当 ×")
