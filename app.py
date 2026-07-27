import streamlit as st
import pandas as pd
import numpy_financial as npf
import plotly.express as px

# 웹 페이지 기본 설정
st.set_page_config(page_title="태양광 발전사업 통합 대시보드", layout="wide")

# ---------------------------------------------------------
# 사이드바: 페이지 선택 및 공통 입력값
# ---------------------------------------------------------
st.sidebar.title("☀️ 태양광 발전사업 분석")
page = st.sidebar.radio("이동할 대시보드 선택", ["1. 사업성 종합 분석", "2. 수익·지출·순수익 시각화"])

st.sidebar.divider()
st.sidebar.header("📝 공통 사업 기본 정보")
project_name = st.sidebar.text_input("사업명", value="춘천 창촌리 태양광발전사업")
location = st.sidebar.text_input("위치", value="강원특별자치도 춘천시 남산면 창촌리")
capacity = st.sidebar.number_input("설비용량 (kW)", value=986.21)
investment = st.sidebar.number_input("총사업비 (원)", value=1972000000, step=10000000)
years = st.sidebar.number_input("사업기간 (년)", value=20, step=1)

st.sidebar.header("📈 발전 및 수익 가정")
price_per_kwh = st.sidebar.number_input("전력 판매단가 (원/kWh)", value=150.0)
initial_efficiency = st.sidebar.number_input("최초 운영 패널 효율 (%)", value=99.0) / 100.0
degradation = st.sidebar.number_input("연간 발전효율 감소율 (%)", value=0.80, format="%.2f") / 100.0

st.sidebar.header("💸 세부 운영비용 (1년 차 기준)")
labor_cost = st.sidebar.number_input("인건비 (원)", value=10000000, step=1000000)
severance_pay = st.sidebar.number_input("퇴직금 (원)", value=1000000, step=100000)
maintenance = st.sidebar.number_input("수선유지비 (원)", value=4000000, step=500000)
land_rent = st.sidebar.number_input("도유지 대부료 (원)", value=0, step=500000)
other_op_cost = st.sidebar.number_input("기타 운영비 (원)", value=0, step=500000)

initial_op_cost = labor_cost + severance_pay + maintenance + land_rent + other_op_cost

st.sidebar.header("📊 재무 가정")
inflation_rate = st.sidebar.number_input("물가상승률 (%)", value=3.11, help="최근 5년(2021~2025) 평균 물가상승률 적용") / 100.0
discount_rate = st.sidebar.number_input("할인율 (%)", value=4.5) / 100.0

# ---------------------------------------------------------
# 공통 계산 엔진 (현금흐름 및 지표 산출)
# ---------------------------------------------------------
first_year_gen = capacity * 3.5 * 365 * initial_efficiency
cash_flows = [-investment]
data = []
cum_cf = -investment
cum_dcf = -investment

for year in range(1, int(years) + 1):
    gen = first_year_gen * ((1 - degradation) ** (year - 1))
    revenue = gen * price_per_kwh  # 수익
    current_op_cost = initial_op_cost * ((1 + inflation_rate) ** (year - 1))  # 지출 (운영비)
    net_cf = revenue - current_op_cost  # 순수익 (현금흐름)
    
    discount_factor = (1 + discount_rate) ** year
    dcf = net_cf / discount_factor
    
    cum_cf += net_cf
    cum_dcf += dcf
    cash_flows.append(net_cf)
    
    data.append([
        year, gen, revenue, current_op_cost, net_cf, cum_cf, dcf, cum_dcf
    ])

df = pd.DataFrame(data, columns=[
    "연도", "발전량(kWh)", "수익(매출액)", "지출(운영비)", "순수익", 
    "누적현금흐름", "할인현금흐름", "누적할인현금흐름"
])

npv = npf.npv(discount_rate, cash_flows)
irr = npf.irr(cash_flows) * 100 if npf.irr(cash_flows) else 0
pv_of_future_cf = npv + investment
pi = pv_of_future_cf / investment if investment > 0 else 0

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
        return df.loc[idx-1, "연도"] + (abs(prev_cum) / current_cf)

simple_payback = calculate_payback(df, "순수익", "누적현금흐름")
discounted_payback = calculate_payback(df, "할인현금흐름", "누적할인현금흐름")

# ---------------------------------------------------------
# 페이지 1: 사업성 종합 분석 대시보드
# ---------------------------------------------------------
if page == "1. 사업성 종합 분석":
    st.title("☀️ 태양광 발전사업 타당성 종합 분석")
    st.markdown(f"### 📍 {project_name} ({location})")
    st.markdown(f"**1년 차 예상 발전량:** `{first_year_gen:,.0f} kWh` (설비용량 {capacity}kW × 3.5시간 × 365일)")
    st.divider()

    st.subheader("💡 핵심 재무 지표")
    col1, col2, col3, col4, col5 = st.columns(5)
    npv_millions = npv / 1_000_000

    col1.metric("NPV (순현재가치)", f"{npv_millions:,.0f} 백만원")
    col2.metric("IRR (내부수익률)", f"{irr:.2f} %")
    col3.metric("PI (수익성지수)", f"{pi:.3f}")
    col4.metric("단순 회수기간", f"{simple_payback:.2f} 년" if isinstance(simple_payback, float) else simple_payback)
    col5.metric("할인 회수기간", f"{discounted_payback:.2f} 년" if isinstance(discounted_payback, float) else discounted_payback)

    st.divider()
    st.subheader("📋 연도별 상세 데이터")
    st.dataframe(df.style.format({
        "발전량(kWh)": "{:,.0f}",
        "수익(매출액)": "{:,.0f}",
        "지출(운영비)": "{:,.0f}",
        "순수익": "{:,.0f}",
        "누적현금흐름": "{:,.0f}",
        "할인현금흐름": "{:,.0f}",
        "누적할인현금흐름": "{:,.0f}"
    }), use_container_width=True)

# ---------------------------------------------------------
# 페이지 2: 수익·지출·순수익 시각화 대시보드 (신규 추가)
# ---------------------------------------------------------
elif page == "2. 수익·지출·순수익 시각화":
    st.title("📊 수익 · 지출 · 순수익 한눈에 보기")
    st.markdown("매년 발생하는 발전 수익, 물가상승이 반영된 지출(운영비), 그리고 최종 순수익의 흐름을 시각적으로 비교합니다.")
    st.divider()

    # 데이터를 그래프용으로 변환 (melt)
    df_melted = df.melt(
        id_vars=["연도"], 
        value_vars=["수익(매출액)", "지출(운영비)", "순수익"],
        var_name="구분", 
        value_name="금액(원)"
    )

    # 그룹 막대그래프 생성
    fig = px.bar(
        df_melted, 
        x="연도", 
        y="금액(원)", 
        color="구분", 
        barmode="group",
        title="연도별 수익, 지출 및 순수익 비교 추이",
        color_discrete_map={
            "수익(매출액)": "#2b8cbe",  # 파란계열
            "지출(운영비)": "#de2d26",  # 빨간계열
            "순수익": "#31a354"          # 초록계열
        }
    )
    fig.update_layout(xaxis_title="운영 연도", yaxis_title="금액 (원)", legend_title="항목")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("📈 순수익 및 누적 현금흐름 추이")
    fig_line = px.line(
        df, 
        x="연도", 
        y=["순수익", "누적현금흐름"], 
        markers=True,
        title="연도별 순수익 및 누적 현금흐름 흐름"
    )
    fig_line.update_layout(xaxis_title="운영 연도", yaxis_title="금액 (원)", legend_title="지표")
    st.plotly_chart(fig_line, use_container_width=True)
