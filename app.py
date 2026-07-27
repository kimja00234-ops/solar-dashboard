import streamlit as st
import pandas as pd
import numpy_financial as npf
import plotly.express as px

st.set_page_config(page_title="태양광 타당성 분석", layout="wide")
st.title("☀️ 태양광 발전사업 타당성 분석")

st.sidebar.header("1. 기본 정보 및 투자비")
capacity = st.sidebar.number_input("설비용량 (kW)", value=986.21)
investment = st.sidebar.number_input("총사업비 (원)", value=1972000000, step=10000000)
years = st.sidebar.number_input("사업기간 (년)", value=20)

st.sidebar.header("2. 수익 및 비용 가정")
smp = st.sidebar.number_input("SMP 단가 (원/kWh)", value=100.0)
rec = st.sidebar.number_input("REC 단가 (원/kWh)", value=50.0)
rec_weight = st.sidebar.number_input("REC 가중치", value=1.2)
sun_hours = st.sidebar.number_input("일 평균 발전시간 (시간)", value=3.5)
degradation = st.sidebar.number_input("연간 발전량 감소율 (%)", value=0.5) / 100.0
op_cost = st.sidebar.number_input("연간 운영비 (원)", value=30000000, step=1000000)
discount_rate = st.sidebar.number_input("할인율 (%)", value=4.5) / 100.0

first_year_gen = capacity * sun_hours * 365
cash_flows = [-investment]
revenues, op_costs = [0], [0]

for year in range(1, int(years) + 1):
    gen = first_year_gen * ((1 - degradation) ** (year - 1))
    rev = gen * (smp + (rec * rec_weight))
    net_cf = rev - op_cost
    revenues.append(rev)
    op_costs.append(op_cost)
    cash_flows.append(net_cf)

df = pd.DataFrame({
    "연도": range(0, int(years) + 1),
    "매출액(원)": revenues,
    "운영비(원)": op_costs,
    "순현금흐름(원)": cash_flows
})
df["누적현금흐름(원)"] = df["순현금흐름(원)"].cumsum()

npv = npf.npv(discount_rate, cash_flows)
irr = npf.irr(cash_flows) * 100 if npf.irr(cash_flows) else 0

st.subheader("💡 분석 결과")
col1, col2 = st.columns(2)
col1.metric("예상 NPV (순현재가치)", f"{npv:,.0f} 원")
col2.metric("예상 IRR (내부수익률)", f"{irr:.2f} %")

fig = px.bar(df[1:], x="연도", y="순현금흐름(원)", title="현금흐름 추이")
fig.add_scatter(x=df["연도"], y=df["누적현금흐름(원)"], mode='lines+markers', name="누적현금흐름")
st.plotly_chart(fig, use_container_width=True)
