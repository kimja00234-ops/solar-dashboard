import streamlit as st
import pandas as pd
import numpy_financial as npf
import plotly.express as px

st.set_page_config(page_title="태양광 타당성 분석 (심화)", layout="wide")
st.title("☀️ 태양광 발전사업 타당성 심화 분석 대시보드")
st.markdown("엑셀의 현금흐름표(인건비, 대부료, 감가상각, 법인세 등)를 완벽히 구현한 버전입니다.")

# ---------------------------------------------------------
# 1. 사이드바 - 입력값 설정 (엑셀 '입력값' 시트 100% 반영)
# ---------------------------------------------------------
st.sidebar.header("1. 기본 정보 및 투자비")
capacity = st.sidebar.number_input("설비용량 (kW)", value=986.21)
investment = st.sidebar.number_input("총사업비 (원)", value=1972000000, step=10000000)
years = st.sidebar.number_input("사업기간 (년)", value=20)
residual_value = st.sidebar.number_input("잔존가치 (원)", value=0)

st.sidebar.header("2. 발전량 및 단가 가정")
sun_hours = st.sidebar.number_input("일 평균 발전시간 (시간)", value=3.5)
degradation = st.sidebar.number_input("연간 발전량 감소율 (%)", value=0.5) / 100.0
smp = st.sidebar.number_input("SMP 단가 (원/kWh)", value=100.0)
rec = st.sidebar.number_input("REC 단가 (원/kWh)", value=50.0)
rec_weight = st.sidebar.number_input("REC 가중치", value=1.2)

st.sidebar.header("3. 연간 운영비 (O&M)")
labor_cost = st.sidebar.number_input("인건비 (원)", value=15000000, step=1000000)
severance_pay = st.sidebar.number_input("퇴직금 (원)", value=1250000, step=100000)
maintenance = st.sidebar.number_input("수선유지비 (원)", value=5000000, step=100000)
land_rent = st.sidebar.number_input("도유지 대부료 (원)", value=8000000, step=100000)

st.sidebar.header("4. 재무 가정")
corporate_tax_rate = st.sidebar.number_input("법인세율 (%)", value=19.0) / 100.0
discount_rate = st.sidebar.number_input("할인율 (%)", value=4.5) / 100.0

# ---------------------------------------------------------
# 2. 계산 엔진 (엑셀 '연도별분석' 시트 완벽 구현)
# ---------------------------------------------------------
first_year_gen = capacity * sun_hours * 365
annual_depreciation = (investment - residual_value) / years # 정액법 감가상각

# 데이터 저장을 위한 리스트
data = []
cash_flows = [-investment] # 0년차 현금흐름

for year in range(1, int(years) + 1):
    # 1. 매출액 산정
    gen = first_year_gen * ((1 - degradation) ** (year - 1))
    price_per_kwh = smp + (rec * rec_weight)
    revenue = gen * price_per_kwh
    
    # 2. 현금운영비 산정
    total_op_cost = labor_cost + severance_pay + maintenance + land_rent
    
    # 3. 과세표준 및 법인세 산정 (엑셀 로직: 영업이익 = 매출액 - 현금운영비 - 감가상각비)
    tax_base = revenue - total_op_cost - annual_depreciation
    if tax_base < 0: tax_base = 0
    corporate_tax = tax_base * corporate_tax_rate
    
    # 4. 세후 프로젝트 현금흐름 = 매출액 - 현금운영비 - 법인세 + 잔존가치(마지막 해)
    net_cf = revenue - total_op_cost - corporate_tax
    if year == int(years):
        net_cf += residual_value
        
    cash_flows.append(net_cf)
    
    # 테이블용 데이터 추가
    data.append([
        year, gen, price_per_kwh, revenue, labor_cost, severance_pay, maintenance, 
        land_rent, total_op_cost, annual_depreciation, tax_base, corporate_tax, net_cf
    ])

# ---------------------------------------------------------
# 3. 데이터프레임 구성 및 재무 지표 도출
# ---------------------------------------------------------
columns = [
    "연도", "발전량(kWh)", "판매단가(원)", "매출액(원)", "인건비(원)", "퇴직금(원)", 
    "수선유지비(원)", "대부료(원)", "현금운영비(원)", "감가상각비(원)", 
    "과세표준(원)", "법인세(원)", "프로젝트현금흐름(원)"
]
df = pd.DataFrame(data, columns=columns)
df.insert(0, "연도", df.pop("연도")) # 연도 컬럼 위치 고정

# 현금흐름 및 할인현금흐름 계산
df["할인계수"] = [1 / ((1 + discount_rate) ** y) for y in df["연도"]]
df["현금흐름현재가치(원)"] = df["프로젝트현금흐름(원)"] * df["할인계수"]
df["누적현금흐름(원)"] = df["프로젝트현금흐름(원)"].cumsum() - investment

# NPV, IRR 계산
npv = npf.npv(discount_rate, cash_flows)
irr = npf.irr(cash_flows) * 100 if npf.irr(cash_flows) else 0

# ---------------------------------------------------------
# 4. 대시보드 화면 출력
# ---------------------------------------------------------
st.subheader("💡 핵심 재무 지표")
col1, col2 = st.columns(2)
col1.metric("예상 NPV (순현재가치)", f"{npv:,.0f} 원")
col2.metric("예상 IRR (내부수익률)", f"{irr:.2f} %")

st.subheader("📊 연도별 누적 현금흐름 및 타당성 추이")
fig = px.bar(df, x="연도", y="프로젝트현금흐름(원)", title="프로젝트 현금흐름 추이")
fig.add_scatter(x=df["연도"], y=df["누적현금흐름(원)"], mode='lines+markers', name="누적현금흐름")
st.plotly_chart(fig, use_container_width=True)

st.subheader("📋 엑셀 연도별 분석표 (세부내역)")
st.dataframe(df.style.format("{:,.0f}"))
