import streamlit as st
import json
from datetime import datetime

# ページ設定
st.set_page_config(
    page_title="扶養控除 判定フロー", 
    layout="wide",
    initial_sidebar_state="expanded"
)

class TaxDeductionCalculator:
    """扶養控除判定のメインクラス"""
    
    def __init__(self):
        self.results = {}
    
    def get_spouse_result(self, main_income_high, spouse_income_range):
        """配偶者の判定結果を取得"""
        if main_income_high:
            result_map = {
                "年収：123万円以下": ("❌ 控除対象外", "✅ 被扶養者対象", "✅ 家族手当支給"),
                "年収：123万円超〜130万円未満": ("❌ 控除対象外", "✅ 被扶養者対象", "✅ 家族手当支給"),
                "年収：130万円超〜160万円未満": ("❌ 控除対象外", "❌ 被扶養者対象外", "✅ 家族手当支給"),
                "年収：160万円超〜201万円未満": ("❌ 控除対象外", "❌ 被扶養者対象外", "❌ 家族手当不支給"),
                "年収：201万円超": ("❌ 控除対象外", "❌ 被扶養者対象外", "❌ 家族手当不支給"),
            }
        else:
            result_map = {
                "年収：123万円以下": ("✅ 配偶者控除対象", "✅ 被扶養者対象", "✅ 家族手当支給"),
                "年収：123万円超〜130万円未満": ("✅ 配偶者特別控除対象", "✅ 被扶養者対象", "✅ 家族手当支給"),
                "年収：130万円超〜160万円未満": ("✅ 配偶者特別控除対象", "❌ 被扶養者対象外", "✅ 家族手当支給"),
                "年収：160万円超〜201万円未満": ("✅ 配偶者特別控除対象　※年末調整にて申請", "❌ 被扶養者対象外", "❌ 家族手当不支給"),
                "年収：201万円超": ("❌ 控除対象外", "❌ 被扶養者対象外", "❌ 家族手当不支給"),
            }
        return result_map.get(spouse_income_range, ("❌ 判定不可", "❌ 判定不可", "❌ 判定不可"))
    
    def get_dependent_result(self, age_group, income_range):
        """扶養親族の判定結果を取得"""
        if age_group == "16歳以下":
            return ("❌ 控除対象外（※住民税は控除対象 ✅）", "✅ 被扶養者対象", "✅ 家族手当支給")
        
        if age_group == "19歳以上23歳未満":
            result_map = {
                "年収：123万円以下": ("✅ 扶養控除対象", "✅ 被扶養者対象", "✅ 家族手当支給"),
                "年収：123万円超〜130万円未満": ("✅ 特定扶養親族特別控除対象", "✅ 被扶養者対象", "✅ 家族手当支給"),
                "年収：130万円超〜160万円未満": ("✅ 特定扶養親族特別控除対象", "❌ 被扶養者対象外", "✅ 家族手当支給"),
                "年収：160万円超〜188万円未満": ("✅ 特定扶養親族特別控除対象（段階的）", "❌ 被扶養者対象外", "❌ 家族手当不支給"),
                "年収：188万円超": ("❌ 控除対象外", "❌ 被扶養者対象外", "❌ 家族手当不支給")
            }
        else:
            result_map = {
                "年収：123万円以下": ("✅ 扶養控除対象", "✅ 被扶養者対象", "✅ 家族手当支給"),
                "年収：123万円超〜130万円未満": ("❌ 控除対象外", "✅ 被扶養者対象", "✅ 家族手当支給"),
                "年収：130万円超〜160万円未満": ("❌ 控除対象外", "❌ 被扶養者対象外", "✅ 家族手当支給"),
                "年収：160万円超〜188万円未満": ("❌ 控除対象外", "❌ 被扶養者対象外", "❌ 家族手当不支給"),
                "年収：188万円超": ("❌ 控除対象外", "❌ 被扶養者対象外", "❌ 家族手当不支給")
            }
        return result_map.get(income_range, ("❌ 判定不可", "❌ 判定不可", "❌ 判定不可"))

@st.cache_data
def load_help_content():
    """ヘルプコンテンツを読み込み"""
    return {
        "配偶者控除": "年収103万円以下の配偶者に対する所得控除です。該当する配偶者がいる納税者は申告することにより、納税者本人の所得税が軽減されます。",
        "配偶者特別控除": "年収103万円超201万円以下の配偶者に対する所得控除です。該当する配偶者がいる納税者は申告することにより、納税者本人の所得税が軽減されます。",
        "扶養控除": "該当する扶養親族がいる納税者は一定の金額の所得控除が受けられます。申告することにより、納税者本人の所得税が軽減されます。",
        "特定扶養親族特別控除": "19歳以上23歳未満の扶養親族に対する所得控除です。通常の扶養控除より控除額が大きくなります。",
        "被扶養者": "健康保険において、年収130万円未満の家族が対象となります。該当の家族は出版健康保険組合の健康保険証が使用できます。",
        "家族手当": "所得税法上の非課税者であるご家族をお持ちの方に支給する、当会独自の手当になります。"
    }

def display_help_section():
    """ヘルプセクションを表示"""
    with st.sidebar:
        # サイドバーの幅を広げるためのCSS
        st.markdown("""
        <style>
        .css-1d391kg {
            width: 400px;
        }
        .css-1cypcdb {
            width: 400px;
        }
        section[data-testid="stSidebar"] {
            width: 400px !important;
        }
        section[data-testid="stSidebar"] > div {
            width: 400px !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.subheader("📖 用語説明")
        help_content = load_help_content()
        
        for term, explanation in help_content.items():
            with st.expander(f"💡 {term}"):
                st.write(explanation)

def display_guidance():
    """手続き案内を表示"""
    st.info("""
    📋 **手続きのご案内**
    
    ご家族の収入が変わり、控除や健保手当等の対象になる/対象から外れる場合は、
    家族変更届とともに必要な書類をご提出ください。
    
    - **控除関連**：扶養控除等（異動）申告書
    - ※年末調整にて申請　となっている場合は提出は不要です。年末調整時に申告ください。

    - **健保関連**：被扶養者（異動）届
    """)

def validate_inputs(person_type, **kwargs):
    """入力値の検証"""
    errors = []
    
    if person_type == "spouse":
        if "main_income" not in kwargs or kwargs["main_income"] is None:
            errors.append("本人の年収を選択してください")
        if "spouse_income" not in kwargs or kwargs["spouse_income"] is None:
            errors.append("配偶者の年収を選択してください")
    
    elif person_type == "dependent":
        if "age_group" not in kwargs or kwargs["age_group"] is None:
            errors.append("対象者の年齢を選択してください")
        if kwargs.get("age_group") != "16歳以下" and ("income" not in kwargs or kwargs["income"] is None):
            errors.append("対象者の年収を選択してください")
    
    return errors

def main():
    # タイトル
    st.title("🧾 手当・健保・税控除　かんたん判定フロー")
    
    # 注意書き
    st.markdown(
        "※ 税の所得控除、健康保険の被扶養者認定、"
        "家族手当支給の可否を簡易的に判定するフローです。年収は給与による収入を想定しています。"
        "年金の場合や、障害者の場合等は変わってきますので、詳細は制度ごとの基準をご確認ください。"
    )
    
    # ヘルプセクション
    display_help_section()
    
    # 計算機インスタンス
    calculator = TaxDeductionCalculator()
    
    st.markdown("---")
    
    # レスポンシブなレイアウト（サイドバーが広くなった分メインコンテンツを調整）
    col1, col2 = st.columns([1, 1], gap="medium")
    
    with col1:
        st.markdown("### 【配偶者に関する判定】")
        
        # STEP 1
        st.subheader("STEP 1：対象者は配偶者ですか？")
        is_spouse = st.radio("", ["はい", "いいえ"], key="spouse_radio")
        
        if is_spouse == "いいえ":
            st.warning("▶ 親族・子どもに関する判定へ進んでください")
        
        # 配偶者パート
        if is_spouse == "はい":
            # STEP 2
            st.subheader("STEP 2：本人の年間収入は1,000万円以上ですか？")
            income_high_option = st.radio("本人の年収は？", ["1,000万円未満", "1,000万円以上"], key="main_income_radio")
            income_high = (income_high_option == "1,000万円以上")
            
            # STEP 3
            st.subheader("STEP 3：配偶者の年間収入（目安）")
            income_range = st.selectbox(
                "配偶者の年収レンジを選択してください", [
                    "選択してください",
                    "年収：123万円以下",
                    "年収：123万円超〜130万円未満",
                    "年収：130万円超〜160万円未満",
                    "年収：160万円超〜201万円未満",
                    "年収：201万円超"
                ],
                key="spouse_income_select"
            )
            
            # 入力検証
            validation_errors = validate_inputs("spouse", 
                                              main_income=income_high_option, 
                                              spouse_income=income_range if income_range != "選択してください" else None)
            
            if validation_errors:
                for error in validation_errors:
                    st.error(f"⚠️ {error}")
            elif income_range != "選択してください":
                # 判定結果の取得と表示
                tax_result, health_result, allowance_result = calculator.get_spouse_result(income_high, income_range)
                
                st.success(f"""
**判定結果：**
- 所得控除：{tax_result}
- 健康保険：{health_result}
- 家族手当：{allowance_result}
""")
                
                # 結果をセッション状態に保存
                st.session_state.spouse_results = {
                    "判定日時": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "対象者": "配偶者",
                    "本人年収": income_high_option,
                    "配偶者年収": income_range,
                    "所得控除": tax_result,
                    "健康保険": health_result,
                    "家族手当": allowance_result
                }
    
    with col2:
        st.markdown("### 【親族・子どもに関する判定】")
        
        st.subheader("STEP 2：対象者の年齢")
        age_group = st.selectbox("対象者の年齢層は？", [
            "選択してください",
            "16歳以下",
            "16歳以上18歳未満もしくは23歳以上",
            "19歳以上23歳未満"
        ], key="age_select")
        
        if age_group == "16歳以下":
            st.info(
                "所得控除：❌ 控除対象外（※住民税は控除対象 ✅）  \n"
                "健康保険：✅ 被扶養者対象  \n"
                "家族手当：✅ 家族手当支給"
            )
            
            # 結果をセッション状態に保存
            st.session_state.dependent_results = {
                "判定日時": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "対象者": "親族・子ども",
                "年齢層": age_group,
                "年収": "該当なし",
                "所得控除": "❌ 控除対象外（※住民税は控除対象 ✅）",
                "健康保険": "✅ 被扶養者対象",
                "家族手当": "✅ 家族手当支給"
            }
            
        elif age_group and age_group != "選択してください":
            st.subheader("STEP 3：対象者の年間収入（目安）")
            income_child = st.selectbox(
                "",
                [
                    "選択してください",
                    "年収：123万円以下",
                    "年収：123万円超〜130万円未満",
                    "年収：130万円超〜160万円未満",
                    "年収：160万円超〜188万円未満",
                    "年収：188万円超"
                ],
                key="child_income_select"
            )
            
            # 入力検証
            validation_errors = validate_inputs("dependent", 
                                              age_group=age_group, 
                                              income=income_child if income_child != "選択してください" else None)
            
            if validation_errors:
                for error in validation_errors:
                    st.error(f"⚠️ {error}")
            elif income_child != "選択してください":
                # 判定結果の取得と表示
                tax_result, health_result, allowance_result = calculator.get_dependent_result(age_group, income_child)
                
                st.success(f"""
**判定結果：**
- 所得控除：{tax_result}
- 健康保険：{health_result}
- 家族手当：{allowance_result}
""")
                
                # 結果をセッション状態に保存
                st.session_state.dependent_results = {
                    "判定日時": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "対象者": "親族・子ども",
                    "年齢層": age_group,
                    "年収": income_child,
                    "所得控除": tax_result,
                    "健康保険": health_result,
                    "家族手当": allowance_result
                }
    
    # 手続き案内
    st.markdown("---")
    display_guidance()

if __name__ == "__main__":
    main()