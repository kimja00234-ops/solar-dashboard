import streamlit as st
import pandas as pd
import numpy_financial as npf
import plotly.express as px

# 웹 페이지 기본 설정
st.set_page_config(page_title="태양광 발전사업 통합 대시보드", layout="wide")

# ---------------------------------------------------------
# 사이드바: 대시보드 페이지 선택 메뉴만 깔끔하게 배치
# ---------------------------------------------------------
st.sidebar.title("☀️ 태양광 발전사업 분석")
page = st.sidebar.radio("이동할 대시보드 선택", ["1. 사업성 종합 분석", "2. 수익·지출·순수익 시각화"])
st.sidebar.divider()
st.sidebar.markdown("💡 메인 화면의 **탭(Tab)**을 통해 입력과 분석 결과를 각각 확인하실 수 있습니다.")

# ---------------------------------------------------------
# 메인 화면: 탭(Tab) 구조를 이용한 입력 영역 및 대시보드 분리
# ---------------------------------------------------------
st.title("☀️ 태양광 발전사업 타당성 자동 분석 프로그램")
st.markdown("입력 항목과 분석 결과를 아래의 **탭**을 통해 각각 확인해 주세요.")

tab1, tab2, tab3 = st.tabs(["📌 1. 사업 기본 정보 및 운영비·가정 입력", "🏢 2. 부지 대부료 산정", "📊 3. 사업성 분석 대시보드"])

with tab1:
    st.subheader("📌 사업 기본 정보 및 발전 가정 입력")
    
    # 구역 1: 사업 기본 정보
    st.markdown("### 🔹 사업 기본 정보")
    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input("사업명", value="춘천 창촌리 태양광발전사업")
        capacity = st.number_input("설비용량 (kW)", value=986.21, format="%.2f")
        land_area_str = st.text_input("부지면적 (㎡)", value="11,557")
        try:
            land_area = float(land_area_str.replace(",", ""))
        except ValueError:
            land_area = 11557.0

    with col2:
        location = st.text_input("위치", value="강원특별자치도 춘천시 남산면 창촌리")
        
        # 총사업비 실시간 콤마 포맷팅 처리
        if 'investment_input' not in st.session_state:
            st.session_state.investment_input = "1,972,000,000"
            
        def update_investment():
            val = st.session_state.investment_widget.replace(",", "").strip()
            if val.isdigit():
                st.session_state.investment_input = f"{int(val):,}"
            else:
                st.session_state.investment_input = val

        investment_str = st.text_input("총사업비 (원)", value=st.session_state.investment_input, key="investment_widget", on_change=update_investment)
        try:
            investment = int(investment_str.replace(",", "").strip()) if investment_str.replace(",", "").strip().isdigit() else 0
        except ValueError:
            investment = 0

        years = st.number_input("사업기간 (년)", value=20, step=1)

    st.divider()

    # 구역 2: 발전 가정량
    st.markdown("### 🔹 발전 가정량")
    col3, col4 = st.columns(2)
    with col3:
        sun_hours = st.number_input("일일 평균 발전시간 (h/day)", value=3.5, format="%.2f")
        initial_efficiency = st.number_input("최초 운영 패널 효율 (%) (기본값 적용)", value=99.0, format="%.2f") / 100.0
        degradation = st.number_input("연간 발전효율 감소율 (%) (기본값 적용)", value=0.80, format="%.2f") / 100.0
    with col4:
        base_annual_gen = capacity * sun_hours * 365
        st.markdown(f"**연간 기준 발전량**")
        st.markdown(f"### `{round(base_annual_gen, -2):,.0f} kWh`")
        st.caption("설비용량 × 일일 평균 발전시간 × 365")
        
        raw_first_year_gen = base_annual_gen * initial_efficiency
        first_year_gen = round(raw_first_year_gen, -2)
        st.markdown(f"**1년차 예상 발전량**")
        st.markdown(f"### `{first_year_gen:,.0f} kWh`")
        st.caption("연간 기준 발전량 × 최초 운영 패널 효율")

    st.divider()
    
    # 구역 3: 재무 및 평가 가정
    st.markdown("### 🔹 재무 및 평가 가정")
    col5, col6 = st.columns(2)
    with col5:
        price_per_kwh = st.number_input("전력 판매단가 (원/kWh)", value=150.0, format="%.2f")
        discount_rate = st.number_input("할인율 (%)", value=4.5, format="%.2f") / 100.0
        inflation_rate = st.number_input("물가상승률 (%)", value=3.11, help="최근 5년(2021~2025) 평균 물가상승률 적용", format="%.2f") / 100.0
    with col6:
        base_annual_revenue = base_annual_gen * price_per_kwh
        first_year_revenue = first_year_gen * price_per_kwh
        
        st.markdown(f"**예상 전력판매수익 (기준)**")
        st.markdown(f"### `{base_annual_revenue:,.0f} 원`")
        st.caption("연간 기준 발전량 × 전력 판매단가")
        
        st.markdown(f"**1년차 예상 전력판매수익**")
        st.markdown(f"### `{first_year_revenue:,.0f} 원`")
        st.caption("1년차 예상 발전량 × 전력 판매단가")

    st.divider()

    # 구역 4: 운영비 정보 (st.number_input으로 완벽하게 원단위 기호 및 콤마 처리 보장)
    st.markdown("### 🔹 운영비 정보")
    st.markdown("운영비 세부 항목 및 비고를 확인하고 필요한 경우 금액을 수정해 주세요.")

    auto_depreciation = int(investment / years) if years > 0 else 0
    auto_maintenance = int(auto_depreciation * 0.10)
    
    # 세션 상태 초기화
    if 'labor_val' not in st.session_state: st.session_state.labor_val = 10000000
    if 'labor_note' not in st.session_state: st.session_state.labor_note = "전기안전관리자(대행) 인건비"
    if 'sev_note' not in st.session_state: st.session_state.sev_note = "인건비 / 12개월"
    if 'dep_note' not in st.session_state: st.session_state.dep_note = "총사업비 / 사업기간"
    if 'maint_note' not in st.session_state: st.session_state.maint_note = "감가상각비의 10%"

    current_labor = int(st.session_state.labor_val)
    auto_severance = int(current_labor / 12)

    # 테이블 헤더 구성
    t_col1, t_col2, t_col3 = st.columns([1.5, 2.5, 3])
    with t_col1: st.markdown("**구분**")
    with t_col2: st.markdown("**연간 금액 (원)**")
    with t_col3: st.markdown("**비고**")

    st.divider()

    # 1. 인건비
    r1_c1, r1_c2, r1_c3 = st.columns([1.5, 2.5, 3])
    with r1_c1: st.markdown("연간 인건비")
    with r1_c2: 
        st.session_state.labor_val = st.number_input("인건비 입력", value=int(st.session_state.labor_val), step=1000000, format="%d", label_visibility="collapsed")
    with r1_c3: 
        labor_note = st.text_input("인건비 비고 입력", value=st.session_state.labor_note, label_visibility="collapsed")

    labor_cost = int(st.session_state.labor_val)

    # 2. 퇴직금
    r2_c1, r2_c2, r2_c3 = st.columns([1.5, 2.5, 3])
    with r2_c1: st.markdown("연간 퇴직금")
    with r2_c2: 
        sev_val = st.number_input("퇴직금 입력", value=auto_severance, step=100000, format="%d", label_visibility="collapsed")
    with r2_c3: 
        severance_note = st.text_input("퇴직금 비고 입력", value=st.session_state.sev_note, label_visibility="collapsed")

    severance_pay = int(sev_val)

    # 3. 감가상각비
    r3_c1, r3_c2, r3_c3 = st.columns([1.5, 2.5, 3])
    with r3_c1: st.markdown("연간 감가상각비")
    with r3_c2: 
        dep_val = st.number_input("감가상각비 입력", value=auto_depreciation, step=1000000, format="%d", label_visibility="collapsed")
    with r3_c3: 
        dep_note = st.text_input("감가상각비 비고 입력", value=st.session_state.dep_note, label_visibility="collapsed")

    depreciation = int(dep_val)

    # 4. 수선유지비
    r4_c1, r4_c2, r4_c3 = st.columns([1.5, 2.5, 3])
    with r4_c1: st.markdown("연간 수선유지비")
    with r4_c2: 
        maint_val = st.number_input("수선유지비 입력", value=auto_maintenance, step=500000, format="%d", label_visibility="collapsed")
    with r4_c3: 
        maint_note = st.text_input("수선유지비 비고 입력", value=st.session_state.maint_note, label_visibility="collapsed")

    maintenance = int(maint_val)

with tab2:
    st.subheader("🏢 공유재산(부지) 도유지 대부료 산정 (다중 필지 고려)")
    num_parcels = st.number_input("대부 필지 수", min_value=1, max_value=10, value=2, step=1)
    
    parcel_data = []
    total_land_rent = 0
    total_land_area = 0

    for i in range(int(num_parcels)):
        st.markdown(f"**--- 필지 {i+1} 정보 ---**")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            p_name = st.text_input(f"필지 {i+1} 지번", value=f"창촌리 610-{136 if i==0 else 72}", key=f"name_{i}")
        with c2:
            p_area = st.number_input(f"필지 {i+1} 면적 (㎡)", value=8000.0 if i==0 else 3557.0, key=f"area_{i}", format="%.2f")
        with c3:
            p_price_str = st.text_input(f"필지 {i+1} 공시지가 (원/㎡)", value="50,000" if i==0 else "45,000", key=f"price_str_{i}")
            try:
                p_price = float(p_price_str.replace(",", ""))
            except ValueError:
                p_price = 0.0
        with c4:
            p_rate = st.number_input(f"필지 {i+1} 대부요율 (%)", value=5.0, key=f"rate_{i}", format="%.2f") / 100.0
        
        p_rent = p_area * p_price * p_rate
        total_land_rent += p_rent
        total_land_area += p_area
        
        parcel_data.append({
            "필지명": p_name,
            "면적(㎡)": p_area,
            "공시지가(원/㎡)": p_price,
            "대부요율(%)": p_rate * 100,
            "연간 대부료(원)": p_rent
        })

    st.info(f"💡 **총 부지면적:** {total_land_area:,.2f} ㎡ / **연간 대부료 합계:** {total_land_rent:,.0f} 원")

    st.divider()
    st.subheader("💸 기타 비용 입력")
    
    c_op5, c_note5 = st.columns([2, 2])
    with c_op5:
        other_val = st.number_input("기타 비용 입력 (원)", value=0, step=500000, format="%d")
        other_op_cost = int(other_val)
    with c_note5:
        other_note = st.text_input("기타 비용 비고", value="기타 예비비 등")

    # 총 운영비 합계 산정
    initial_op_cost = labor_cost + severance_pay + depreciation + maintenance + total_land_rent + other_op_cost
    st.success(f"💰 **1년 차 총 운영비 합계 (대부료 포함):** {initial_op_cost:,.0f} 원")

# ---------------------------------------------------------
# 공통 계산 엔진 (현금흐름 및 지표 산출)
# ---------------------------------------------------------
cash_flows = [-investment]
data = []
cum_cf = -investment
cum_dcf = -investment

for year in range(1, int(years) + 1):
    gen = round(first_year_gen * ((1 - degradation) ** (year - 1)), -1)
    revenue = gen * price_per_kwh
    current_op_cost = initial_op_cost * ((1 + inflation_rate) ** (year - 1))
    net_cf = revenue - current_op_cost
    
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
# Tab 3: 사업성 분석 대시보드
# ---------------------------------------------------------
with tab3:
    st.subheader("📊 사업성 분석 결과 대시보드")
    st.markdown(f"### 📍 {project_name} ({location})")
    st.markdown(f"**1년차 예상 발전량:** `{first_year_gen:,.0f} kWh` (연간 기준 발전량 × 최초 운영 패널 효율, 십의 자리 반올림)")
    st.divider()

    st.subheader("🏢 다중 필지 대부료 산정 내역")
    df_parcels = pd.DataFrame(parcel_data)
    st.dataframe(df_parcels.style.format({
        "면적(㎡)": "{:,.2f}",
        "공시지가(원/㎡)": "{:,.0f}",
        "대부요율(%)": "{:.2f}%",
        "연간 대부료(원)": "{:,.0f}"
    }), use_container_width=True)
    st.markdown(f"**총 대부료 합계 (1년 차):** `{total_land_rent:,.0f} 원` (운영비에 자동 반영됨)")
    st.divider()

    st.subheader("💡 핵심 재무 지표")
    col1, col2, col3, col4, col5 = st.columns(5)
    npv_millions = npv / 1_000_000

    col1.metric("NPV (순현재가치)", f"{npv_millions:,.0f} 백만원")
    col2.metric("IRR (내부수익률)", f"{irr:.2f} %")
    col3.metric("PI (수익성지수)", f"{pi:.3f}")
    col4.metric("단순 회수기간", f"{simple_payback:.2f} 년" if isinstance(simple_payback, float) else simple_payback)
    col5.metric("할인 회수기간", f"{discounted_payback:.2f} 년" if isinstance(discounted_payback, float) else discounted_paybox if 'discounted_paybox' in locals() else discounted_payback)

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
# 페이지 2: 수익·지출·순수익 시각화 대시보드
# ---------------------------------------------------------
if page == "2. 수익·지출·순수익 시각화":
    st.title("📊 수익 · 지출 · 순수익 한눈에 보기")
    st.markdown("매년 발생하는 발전 수익, 대부료 및 물가상승이 반영된 지출(운영비), 그리고 최종 순수익의 흐름을 시각적으로 비교합니다.")
    st.divider()

    df_melted = df.melt(
        id_vars=["연도"], 
        value_vars=["수익(매출액)", "지출(운영비)", "순수익"],
        var_name="구분", 
        value_name="금액(원)"
    )

    fig = px.bar(
        df_melted, 
        x="연도", 
        y="금액(원)", 
        color="구분", 
        barmode="group",
        title="연도별 수익, 지출 및 순수익 비교 추이",
        color_discrete_map={
            "수익(매출액)": "#2b8cbe",
            "지출(운영비)": "#de2d26",
            "순수익": "#31a354"
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
