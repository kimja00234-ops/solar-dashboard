import streamlit as st
import pandas as pd
import numpy_financial as npf

# 웹 페이지 기본 설정
st.set_page_config(page_title="태양광 타당성 자동 분석기", layout="wide")
st.title("☀️ 태양광 발전사업 타당성 자동 분석 프로그램")
st.markdown("기본 정보와 단가를 입력하면 NPV, IRR, PI 및 회수기간을 자동으로 계산합니다.")

# ---------------------------------------------------------
# 1. 사이드바 - 사용자 입력창 구성
# ---------------------------------------------------------
st.sidebar.header("1. 사업 기본 정보")
project_name = st.sidebar.text_input("사업명", value="춘천 창촌리 태양광발전사업")
location = st.sidebar.text_input("위치", value="강원특별자치도 춘천시 남산면 창촌리")
capacity = st.sidebar.number_input("설비용량 (kW)", value=986.21)
investment = st.sidebar.number_input("총사업비 (원)", value=1972000000, step=10000000)
years = st.sidebar.number_input("사업기간 (년)", value=20, step=1)

st.sidebar.header("2. 발전 및 수익 가정")
price_per_kwh = st.sidebar.number_input("전력 판매단가 (원/kWh)", value=150.0, help="SMP와 REC가 모두 포함된 최종 판매단가")
initial_efficiency = st.sidebar.number_input("최초 운영 패널 효율 (%)", value=99.0) / 100.0
degradation = st.sidebar.number_input("연간 발전효율 감소율 (%)", value=0.80, format="%.2f") / 100.0

st.sidebar.header("3. 재무 가정")
inflation_rate = st.sidebar.number_input("물가상승률 (%)", value=3.11, help="최근 5년(2021~2025) 평균 물가상승률 적용") / 100.0
op_cost = st.sidebar.number_input("초기 연간 운영비 (원)", value=15000000, step=1000000, help="매년 설정한 물가상승률만큼 운영비가 증가합니다.")
discount_rate = st.sidebar.number_input("할인율 (%)", value=4.5) / 100.0

# ---------------------------------------------------------
# 2. 발전량 및 현금흐름 자동 계산 로직
# ---------------------------------------------------------
# 1년 차 발전량 = 설비용량 x 일발전시간(3.5) x 365 x 최초운영효율
first_year_gen = capacity * 3.5 * 365 * initial_efficiency

cash_flows = [-investment]
data = []
cum_cf = -investment
cum_dcf = -investment

for year in range(1, int(years) + 1):
    # 연도별 발전량 (효율 감소율 반영)
    gen = first_year_gen * ((1 - degradation) ** (year - 1))
    
    # 매출액 계산
    revenue = gen * price_per_kwh
    
    # 당해 연도 운영비 계산 (초기 운영비에 물가상승률 복리 적용)
    current_op_cost = op_cost * ((1 + inflation_rate) ** (year - 1))
    
    # 순현금흐름 계산
    net_cf = revenue - current_op_cost
    
    # 할인 현금흐름(현재가치) 계산
    discount_factor = (1 + discount_rate) ** year
    dcf = net_cf / discount_factor
    
    # 누적 계산
    cum_cf += net_cf
    cum_dcf += dcf
    
    cash_flows.append(net_cf)
    
    # 테이블 표출을 위한 데이터 수집
    data.append([
        year, gen, revenue, current_op_cost, net_cf, cum_cf, dcf, cum_dcf
    ])

df = pd.DataFrame(data, columns=[
    "연도", "발전량(kWh)", "매출액(원)", "운영비(원)", "순현금흐름(원)", 
    "누적현금흐름(원)", "할인현금흐름(원)", "누적할인현금흐름(원)"
])

# ---------------------------------------------------------
# 3. 핵심 재무 지표 (NPV, IRR, PI, 회수기간) 도출
# ---------------------------------------------------------
npv = npf.npv(discount_rate, cash_flows)
irr = npf.irr(cash_flows) * 100 if npf.irr(cash_flows) else 0

# PI (수익성 지수) = (NPV + 총투자비) / 총투자비
pv_of_future_cf = npv + investment
pi = pv_of_future_cf / investment if investment > 0 else 0

# 회수기간(Payback Period) 계산 함수
def calculate_payback(df, cf_col, cum_col):
    positive_mask = df[cum_col] > 0
    if not positive_mask.any():
        return "회수 불가"
    
    idx = positive_mask.idxmax()
    if idx == 0:
        return 0 + abs(-investment) / df.loc[idx, cf_col]
    else:
        prev_cum = df.loc[idx-1, cum_col]
        current_cf = df.loc[idx, cf_col]
        fraction = abs(prev_cum) / current_cf
        return df.loc[idx-1, "연도"] + fraction

simple_payback = calculate_payback(df, "순현금흐름(원)", "누적현금흐름(원)")
discounted_payback = calculate_payback(df, "할인현금흐름(원)", "누적할인현금흐름(원)")

# ---------------------------------------------------------
# 4. 화면 출력 (대시보드)
# ---------------------------------------------------------
st.markdown(f"### 📍 {project_name} ({location})")
st.markdown(f"**1년 차 예상 발전량:** `{first_year_gen:,.0f} kWh` (설비용량 {capacity}kW × 3.5시간 × 365일 × 최초 효율 {initial_efficiency*100}%)")
st.divider()

st.subheader("💡 타당성 분석 결과")
col1, col2, col3, col4, col5 = st.columns(5)

# NPV 단위를 백만원으로 변환
npv_millions = npv / 1_000_000

col1.metric("NPV (순현재가치)", f"{npv_millions:,.0f} 백만원")
col2.metric("IRR (내부수익률)", f"{irr:.2f} %")
col3.metric("PI (수익성지수)", f"{pi:.3f}")
col4.metric("단순 회수기간", f"{simple_payback:.2f} 년" if isinstance(simple_payback, float) else simple_payback)
col5.metric("할인 회수기간", f"{discounted_payback:.2f} 년" if isinstance(discounted_payback, float) else discounted_payback)

st.divider()
st.subheader("📋 연도별 상세 데이터")
# 소수점 및 단위 서식 지정하여 표 출력
st.dataframe(df.style.format({
    "발전량(kWh)": "{:,.0f}",
    "매출액(원)": "{:,.0f}",
    "운영비(원)": "{:,.0f}",
    "순현금흐름(원)": "{:,.0f}",
    "누적현금흐름(원)": "{:,.0f}",
    "할인현금흐름(원)": "{:,.0f}",
    "누적할인현금흐름(원)": "{:,.0f}"
}), use_container_width=True)
