import streamlit as st

st.set_page_config(page_title="扶養控除 判定フロー", layout="wide")
st.title("🧾 手当・健保・税控除　かんたん判定フロー")

st.markdown("---")
st.markdown("### 【配偶者に関する判定】")

# STEP 1
is_spouse = st.radio("STEP 1：対象者は配偶者ですか？", ["はい", "いいえ"])
if is_spouse == "いいえ":
    st.warning("▶ 親族・子どもに関する判定へ進んでください")

# 配偶者パート
if is_spouse == "はい":
    st.subheader("STEP 2：本人の年間収入は1,000万円以上ですか？")
    income_high = st.radio("本人の年収は？", ["1,000万円未満", "1,000万円以上"])

    st.subheader("STEP 3：配偶者の年間収入（目安）")
    income_range = st.selectbox("配偶者の年収（おおよそ）", [
        "年収：123万円以下",
        "年収：123万円超〜130万円未満",
        "年収：130万円超〜160万円未満",
        "年収：160万円超〜201万円未満",
        "年収：201万円超"
    ])

    # マッピング辞書
    if income_high == "1,000万円以上":
        result_map = {
            "年収：123万円以下":      ("❌ 控除対象外", "✅ 被扶養者対象", "✅ 家族手当支給"),
            "年収：123万円超〜130万円未満": ("❌ 控除対象外", "✅ 被扶養者対象", "✅ 家族手当支給"),
            "年収：130万円超〜160万円未満": ("❌ 控除対象外", "❌ 被扶養者対象外", "✅ 家族手当支給"),
            "年収：160万円超〜201万円未満": ("❌ 控除対象外", "❌ 被扶養者対象外", "❌ 家族手当不支給"),
            "年収：201万円超":        ("❌ 控除対象外", "❌ 被扶養者対象外", "❌ 家族手当不支給"),
        }
    else:
        result_map = {
            "年収：123万円以下":      ("✅ 配偶者控除対象", "✅ 被扶養者対象", "✅ 家族手当支給"),
            "年収：123万円超〜130万円未満": ("✅ 配偶者特別控除対象", "✅ 被扶養者対象", "✅ 家族手当支給"),
            "年収：130万円超〜160万円未満": ("✅ 配偶者特別控除対象", "❌ 被扶養者対象外", "✅ 家族手当支給"),
            "年収：160万円超〜201万円未満": ("✅ 配偶者特別控除対象（段階的）", "❌ 被扶養者対象外", "❌ 家族手当不支給"),
            "年収：201万円超":        ("✅ 配偶者特別控除対象（段階的）", "❌ 被扶養者対象外", "❌ 家族手当不支給"),
        }

    if income_range in result_map:
        st.success(f"""
**判定結果：**

- 所得控除：{result_map[income_range][0]}
- 健康保険：{result_map[income_range][1]}
- 家族手当：{result_map[income_range][2]}
        """)

# --- 親族・子どもパート ---
st.markdown("---")
st.markdown("### 【親族・子どもに関する判定】")

st.subheader("STEP 2：対象者の年齢")
age_group = st.selectbox("対象者の年齢層は？", [
    "16歳以下",
    "19〜22歳",
    "それ以外"
])

if age_group == "16歳以下":
    st.info("""16歳以下は以下のとおり：  
- ❌ 所得税控除対象外（※住民税は控除対象 ✅）  
- ✅ 被扶養者対象  
- ✅ 家族手当支給""")
else:
    st.subheader("STEP 3：対象者の年間収入（目安）")
    income_child = st.selectbox("", [
        "年収：123万円以下",
        "年収：123万円超〜130万円未満",
        "年収：130万円超〜160万円未満",
        "年収：160万円超〜188万円未満",
        "年収：188万円超"
    ])

    if age_group == "19〜22歳":
        result_map_child = {
            "年収：123万円以下":      ("✅ 特定扶養控除対象", "✅ 被扶養者対象", "✅ 家族手当支給"),
            "年収：123万円超〜130万円未満": ("✅ 特定扶養控除対象", "✅ 被扶養者対象", "✅ 家族手当支給"),
            "年収：130万円超〜160万円未満": ("✅ 特定扶養控除対象", "❌ 被扶養者対象外", "✅ 家族手当支給"),
            "年収：160万円超〜188万円未満": ("✅ 特定扶養控除対象（段階的）", "❌ 被扶養者対象外", "❌ 家族手当不支給"),
            "年収：188万円超":        ("❌ 控除対象外", "❌ 被扶養者対象外", "❌ 家族手当不支給")
        }
    else:
        result_map_child = {
            "年収：123万円以下":      ("✅ 控除対象扶養親族", "✅ 被扶養者対象", "✅ 家族手当支給"),
            "年収：123万円超〜130万円未満": ("❌ 控除対象外", "✅ 被扶養者対象", "✅ 家族手当支給"),
            "年収：130万円超〜160万円未満": ("❌ 控除対象外", "❌ 被扶養者対象外", "✅ 家族手当支給"),
            "年収：160万円超〜188万円未満": ("❌ 控除対象外", "❌ 被扶養者対象外", "❌ 家族手当不支給"),
            "年収：188万円超":        ("❌ 控除対象外", "❌ 被扶養者対象外", "❌ 家族手当不支給")
        }

    if income_child in result_map_child:
        st.success(f"""
**判定結果：**

- 所得控除：{result_map_child[income_child][0]}
- 健康保険：{result_map_child[income_child][1]}
- 家族手当：{result_map_child[income_child][2]}
        """)
