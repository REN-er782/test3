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
                "年収：160万円超〜201万円未満": ("✅ 配偶者特別控除対象（段階的）", "❌ 被扶養者対象外", "❌ 家族手当不支給"),
                "年収：201万円超": ("✅ 配偶者特別控除対象（段階的）", "❌ 被扶養者対象外", "❌ 家族手当不支給"),
            }
        return result_map.get(spouse_income_range, ("❌ 判定不可", "❌ 判定不可", "❌ 判定不可"))
    
    def get_dependent_result(self, age_group, income_range):
        """扶養親族の判定結果を取得"""
        if age_group == "16歳以下":
            return ("❌ 控除対象外（※住民税は控除対象 ✅）", "✅ 被扶養者対象", "✅ 家族手当支給")
        
        if age_group == "19歳以上23歳未満":
            result_map = {
                "年収：123万円以下": ("✅ 控除対象扶養親族", "✅ 被扶養者対象", "✅ 家族手当支給"),
                "年収：123万円超〜130万円未満": ("✅ 特定扶養控除対象", "✅ 被扶養者対象", "✅ 家族手当支給"),
                "年収：130万円超〜160万円未満": ("✅ 特定扶養控除対象", "❌ 被扶養者対象外", "✅ 家族手当支給"),
                "年収：160万円超〜188万円未満": ("✅ 特定扶養控除対象（段階的）", "❌ 被扶養者対象外", "❌ 家族手当不支給"),
                "年収：188万円超": ("❌ 控除対象外", "❌ 被扶養者対象外", "❌ 家族手当不支給")
            }
        else:
            result_map = {
                "年収：123万円以下": ("✅ 控除対象扶養親族", "✅ 被扶養者対象", "✅ 家族手当支給"),
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
        "配偶者控除": "年収103万円以下の配偶者に対する所得控除です。本人の年収が1,000万円以上の場合は適用されません。",
        "配偶者特別控除": "年収103万円超201万円以下の配偶者に対する所得控除です。収入に応じて段階的に控除額が決まります。",
        "被扶養者": "健康保険において、年収130万円未満（60歳以上または障害者は180万円未満）の家族が対象となります。",
        "特定扶養控除": "19歳以上23歳未満の扶養親族に対する所得控除で、通常の扶養控除より控除額が大きくなります。"
    }

def display_help_section():
    """ヘルプセクションを表示"""
    with st.sidebar:
        st.subheader("📖 用語説明")
        help_content = load_help_content()
        
        for term, explanation in help_content.items():
            with st.expander(f"💡 {term}"):
                st.write(explanation)

def export_results(results_data):
    """結果をJSON形式でエクスポート"""
    results_json = json.dumps(results_data, ensure_ascii=False, indent=2)
    st.download_button(
        label="📥 判定結果をダウンロード",
        data=results_json,
        file_name=f"扶養判定結果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

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
    
    # レスポンシブなレイアウト
    col1, col2 = st.columns([1, 1])
    
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
            "19歳以上23歳未満",
            "16歳以上18歳未満もしくは23歳以上"
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
    
    # エクスポート機能
    st.markdown("---")
    st.subheader("📤 結果のエクスポート")
    
    export_data = {}
    if hasattr(st.session_state, 'spouse_results'):
        export_data["配偶者の判定結果"] = st.session_state.spouse_results
    if hasattr(st.session_state, 'dependent_results'):
        export_data["親族・子どもの判定結果"] = st.session_state.dependent_results
    
    if export_data:
        export_results(export_data)
        st.success("✅ 判定結果が保存されました。上記ボタンからダウンロードできます。")
    else:
        st.info("ℹ️ 判定を完了すると、結果をダウンロードできます。")

if __name__ == "__main__":
    main()
