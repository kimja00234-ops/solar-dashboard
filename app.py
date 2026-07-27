import numpy_financial as npf
import pandas as pd
import plotly.express as px
import streamlit as st

# 웹 페이지 기본 설정
st.set_page_config(page_title="태양광 발전사업 통합 대시보드", layout="wide")

# ---------------------------------------------------------
# 사이드바: 대시보드 페이지 선택 메뉴만 깔끔하게 배치
# ---------------------------------------------------------
st.sidebar.title("☀️ 태양광 발전사업 분석")
page = st.sidebar.radio(
    "이동할 대시보드 선택",
    ["1. 사업성 종합 분석", "2. 수익·지출·순수익 시각화"],
)
st.sidebar.divider()
st.sidebar.markdown(
    "💡 메인 화면의 **탭(Tab)**을 통해 입력과 분석 결과를 각각 확인하실 수 있습니다."
)

# ---------------------------------------------------------
# 메인 화면: 탭(Tab) 구조를 이용한 입력 영역 및 대시보드 분리
# ---------------------------------------------------------
st.title("☀️ 태양광 발전사업 타당성 자동 분석 프로그램")
st.markdown("입력 항목과 분석 결과를 아래의 **탭**을 통해 각각 확인해 주세요.")

tab1, tab2, tab3 = st.tabs([
    "📌 1. 사업 기본 정보 및 운영비·가정 입력",
    "🏢 2. 부지 대부료 산정",
    "📊 3. 연도별 분석 (Sheet 3 연동)",
])

# ---------------------------------------------------------
# Tab 1: 사업 기본 정보 및 운영비 입력
# ---------------------------------------------------------
with tab1:
  st.subheader("📌 사업 기본 정보 및 발전 가정 입력")

  # ✅ Tab1 부지면적 변경 시 Tab2 필지1 면적 세션 상태 자동 업데이트 함수
  def sync_land_area():
    val_str = st.session_state.land_area_widget.replace(",", "").strip()
    try:
      val = float(val_str) if val_str else 0.0
    except ValueError:
      val = 0.0
    st.session_state.area_0 = val

  col1, col2 = st.columns(2)
  with col1:
    project_name = st.text_input(
        "사업명", value="", placeholder="사업명을 입력하세요"
    )

    capacity_val = st.number_input(
        "설비용량 (kW)", value=None, format="%.2f", placeholder="0.00"
    )
    capacity = capacity_val if capacity_val is not None else 0.0

    # ✅ 부지면적 입력 시 on_change 함수로 tab2 필지 1 면적 동기화
    land_area_str = st.text_input(
        "부지면적 (㎡)",
        value="",
        key="land_area_widget",
        on_change=sync_land_area,
        placeholder="예: 11,557",
    )
    try:
      land_area = (
          float(land_area_str.replace(",", "").strip())
          if land_area_str.strip()
          else 0.0
      )
    except ValueError:
      land_area = 0.0

  with col2:
    location = st.text_input("위치", value="", placeholder="위치를 입력하세요")

    if "investment_input" not in st.session_state:
      st.session_state.investment_input = ""

    def update_investment():
      val = st.session_state.investment_widget.replace(",", "").strip()
      if val.isdigit():
        st.session_state.investment_input = f"{int(val):,}"
      else:
        st.session_state.investment_input = val

    investment_str = st.text_input(
        "총사업비 (원)",
        value=st.session_state.investment_input,
        key="investment_widget",
        on_change=update_investment,
        placeholder="예: 1,972,000,000",
    )
    try:
      clean_inv = investment_str.replace(",", "").strip()
      investment = int(clean_inv) if clean_inv.isdigit() else 0
    except ValueError:
      investment = 0

    years_val = st.number_input(
        "사업기간 (년)",
        value=None,
        min_value=1,
        max_value=50,
        step=1,
        placeholder="20",
    )
    years = int(years_val) if years_val is not None else 0

  st.divider()

  st.markdown("### 🔹 발전 가정량")
  col3, col4 = st.columns(2)
  with col3:
    sun_hours = st.number_input(
        "일일 평균 발전시간 (h/day)", value=3.5, format="%.2f"
    )
    initial_efficiency = (
        st.number_input(
            "최초 운영 패널 효율 (%) (기본값 적용)", value=99.0, format="%.2f"
        )
        / 100.0
    )
    degradation = (
        st.number_input(
            "연간 발전효율 감소율 (%) (기본값 적용)", value=0.80, format="%.2f"
        )
        / 100.0
    )
  with col4:
    base_annual_gen = capacity * sun_hours * 365
    st.markdown("**연간 기준 발전량**")
    st.markdown(f"### `{round(base_annual_gen, -2):,.0f} kWh`")
    st.caption("설비용량 × 일일 평균 발전시간 × 365")

    raw_first_year_gen = base_annual_gen * initial_efficiency
    first_year_gen = round(raw_first_year_gen, -2)
    st.markdown("**1년차 예상 발전량**")
    st.markdown(f"### `{first_year_gen:,.0f} kWh`")
    st.caption("연간 기준 발전량 × 최초 운영 패널 효율")

  st.divider()

  st.markdown("### 🔹 재무 및 평가 가정")
  col5, col6 = st.columns(2)
  with col5:
    price_val = st.number_input(
        "전력 판매단가 (원/kWh)",
        value=None,
        format="%.2f",
        placeholder="예: 171.00",
    )
    price_per_kwh = price_val if price_val is not None else 0.0

    discount_rate = (
        st.number_input("할인율 (%)", value=4.5, format="%.2f") / 100.0
    )
    inflation_rate = (
        st.number_input(
            "물가상승률 (%)",
            value=3.11,
            help="최근 5년 평균 물가상승률 적용",
            format="%.2f",
        )
        / 100.0
    )
  with col6:
    base_annual_revenue = base_annual_gen * price_per_kwh
    first_year_revenue = first_year_gen * price_per_kwh

    st.markdown("**예상 전력판매수익 (기준)**")
    st.markdown(f"### `{base_annual_revenue:,.0f} 원`")
    st.caption("연간 기준 발전량 × 전력 판매단가")

    st.markdown("**1년차 예상 전력판매수익**")
    st.markdown(f"### `{first_year_revenue:,.0f} 원`")
    st.caption("1년차 예상 발전량 × 전력 판매단가")

# ---------------------------------------------------------
# Tab 2: 부지 대부료 산정 (세션 상태 동기화)
# ---------------------------------------------------------
with tab2:
  st.subheader("🏢 공유재산(부지) 도유지 대부료 산정 (다중 필지 고려)")
  st.caption(
      "※ 산정 공식: 공시지가 × 부지면적 × 대부요율(5%) × (1 - 경감률 50%)"
  )

  num_parcels = st.number_input(
      "대부 필지 수", min_value=1, max_value=10, value=1, step=1
  )

  parcel_data = []
  total_land_rent = 0
  total_land_area = 0

  # ✅ 필지 1 면적 세션 상태 초기화 (Tab1의 입력값 또는 0.0)
  if "area_0" not in st.session_state:
    st.session_state.area_0 = land_area

  for i in range(int(num_parcels)):
    st.markdown(f"**--- 필지 {i+1} 정보 ---**")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
      p_name = st.text_input(
          f"필지 {i+1} 지번",
          value=f"창촌리 610-{136 if i==0 else 72}",
          key=f"name_{i}",
      )
    with c2:
      # ✅ 필지별 key 세션 관리로 실시간 연동 및 사용자 직접 수정 가능
      if f"area_{i}" not in st.session_state:
        st.session_state[f"area_{i}"] = 3557.0 if i > 0 else land_area

      p_area = st.number_input(
          f"필지 {i+1} 면적 (㎡)",
          key=f"area_{i}",
          format="%.2f",
      )
    with c3:
      p_price_str = st.text_input(
          f"필지 {i+1} 공시지가 (원/㎡)",
          value="50,000" if i == 0 else "45,000",
          key=f"price_str_{i}",
      )
      try:
        p_price = float(p_price_str.replace(",", ""))
      except ValueError:
        p_price = 0.0
    with c4:
      p_rate = (
          st.number_input(
              f"필지 {i+1} 대부요율 (%)",
              value=5.0,
              key=f"rate_{i}",
              format="%.2f",
          )
          / 100.0
      )
    with c5:
      p_discount = (
          st.number_input(
              f"필지 {i+1} 경감률 (%)",
              value=50.0,
              key=f"discount_{i}",
              format="%.2f",
          )
          / 100.0
      )

    p_rent = p_area * p_price * p_rate * (1 - p_discount)
    total_land_rent += p_rent
    total_land_area += p_area

    parcel_data.append({
        "필지명": p_name,
        "면적(㎡)": p_area,
        "공시지가(원/㎡)": p_price,
        "대부요율(%)": p_rate * 100,
        "경감률(%)": p_discount * 100,
        "연간 대부료(원)": p_rent,
    })

  st.info(
      f"💡 **총 부지면적:** {total_land_area:,.2f} ㎡ / **연간 대부료 합계"
      f" (경감률 반영):** {total_land_rent:,.0f} 원"
  )

  st.divider()
  st.subheader("📋 다중 필지 대부료 산정 상세 내역")
  df_parcels = pd.DataFrame(parcel_data)
  st.dataframe(
      df_parcels.style.format({
          "면적(㎡)": "{:,.2f}",
          "공시지가(원/㎡)": "{:,.0f}",
          "대부요율(%)": "{:.2f}%",
          "경감률(%)": "{:.2f}%",
          "연간 대부료(원)": "{:,.0f}",
      }),
      use_container_width=True,
  )

# ---------------------------------------------------------
# Tab 1 잔여 영역: 운영비 정보 세부 처리
# ---------------------------------------------------------
with tab1:
  st.divider()
  st.markdown("### 🔹 운영비 정보")
  st.markdown(
      "운영비 세부 항목 및 비고를 확인하고 필요한 경우 금액을 수정해 주세요."
  )

  auto_depreciation = int(investment / years) if years > 0 else 0
  auto_maintenance = int(auto_depreciation * 0.05)

  if "labor_input" not in st.session_state:
    st.session_state.labor_input = "2,400,000"

  def update_labor():
    val = st.session_state.labor_widget.replace(",", "").strip()
    if val.isdigit():
      st.session_state.labor_input = f"{int(val):,}"
    else:
      st.session_state.labor_input = val

  try:
    labor_cost = (
        int(st.session_state.labor_input.replace(",", "").strip())
        if st.session_state.labor_input.replace(",", "").strip().isdigit()
        else 2400000
    )
  except ValueError:
    labor_cost = 2400000

  auto_severance = int(labor_cost / 12)
  depreciation = auto_depreciation
  maintenance_cost_1st_year = auto_maintenance
  land_rent_cost = total_land_rent

  total_deductible_expenses = (
      labor_cost
      + auto_severance
      + depreciation
      + maintenance_cost_1st_year
      + land_rent_cost
  )
  annual_taxable_income = first_year_revenue - total_deductible_expenses

  if annual_taxable_income > 0:
    if annual_taxable_income <= 200000000:
      calculated_tax = int(annual_taxable_income * 0.09)
    else:
      calculated_tax = int(
          200000000 * 0.09 + (annual_taxable_income - 200000000) * 0.19
      )
  else:
    calculated_tax = 0

  corporate_tax = calculated_tax

  if "labor_note" not in st.session_state:
    st.session_state.labor_note = "전기안전관리자(대행) 인건비"
  if "sev_note" not in st.session_state:
    st.session_state.sev_note = "인건비 / 12개월"
  if "dep_note" not in st.session_state:
    st.session_state.dep_note = "총사업비 / 사업기간"
  if "maint_note" not in st.session_state:
    st.session_state.maint_note = (
        "감가상각비의 5% 적용 (이후 연도별 물가상승률 적용)"
    )
  if "rent_note" not in st.session_state:
    st.session_state.rent_note = (
        "공유재산 대부료 산정 (대부요율 5%, 경감률 50% 적용)"
    )
  if "tax_note" not in st.session_state:
    st.session_state.tax_note = (
        "세전 순이익 기준 법인세 자동 산정 (중소기업 세율 반영)"
    )

  t_col1, t_col2, t_col3 = st.columns([1.5, 2.5, 3])
  with t_col1:
    st.markdown("**구분**")
  with t_col2:
    st.markdown("**연간 금액 (원)**")
  with t_col3:
    st.markdown("**비고**")

  st.divider()

  r1_c1, r1_c2, r1_c3 = st.columns([1.5, 2.5, 3])
  with r1_c1:
    st.markdown("연간 인건비")
  with r1_c2:
    labor_str = st.text_input(
        "인건비 입력",
        value=st.session_state.labor_input,
        key="labor_widget",
        on_change=update_labor,
        label_visibility="collapsed",
    )
  with r1_c3:
    labor_note = st.text_input(
        "인건비 비고 입력",
        value=st.session_state.labor_note,
        label_visibility="collapsed",
    )

  r2_c1, r2_c2, r2_c3 = st.columns([1.5, 2.5, 3])
  with r2_c1:
    st.markdown("연간 퇴직금")
  with r2_c2:
    st.markdown(f"**{auto_severance:,.0f} 원**")
  with r2_c3:
    severance_note = st.text_input(
        "퇴직금 비고 입력",
        value=st.session_state.sev_note,
        label_visibility="collapsed",
    )

  severance_pay = auto_severance

  r3_c1, r3_c2, r3_c3 = st.columns([1.5, 2.5, 3])
  with r3_c1:
    st.markdown("연간 감가상각비")
  with r3_c2:
    st.markdown(f"**{auto_depreciation:,.0f} 원**")
  with r3_c3:
    dep_note = st.text_input(
        "감가상각비 비고 입력",
        value=st.session_state.dep_note,
        label_visibility="collapsed",
    )

  r4_c1, r4_c2, r4_c3 = st.columns([1.5, 2.5, 3])
  with r4_c1:
    st.markdown("연간 수선유지비")
  with r4_c2:
    st.markdown(f"**{maintenance_cost_1st_year:,.0f} 원**")
  with r4_c3:
    maint_note = st.text_input(
        "수선유지비 비고 입력",
        value=st.session_state.maint_note,
        label_visibility="collapsed",
    )

  r5_c1, r5_c2, r5_c3 = st.columns([1.5, 2.5, 3])
  with r5_c1:
    st.markdown("대부료")
  with r5_c2:
    st.markdown(f"**{total_land_rent:,.0f} 원**")
  with r5_c3:
    rent_note = st.text_input(
        "대부료 비고 입력",
        value=st.session_state.rent_note,
        label_visibility="collapsed",
    )

  r6_c1, r6_c2, r6_c3 = st.columns([1.5, 2.5, 3])
  with r6_c1:
    st.markdown("법인세")
  with r6_c2:
    st.markdown(f"**{corporate_tax:,.0f} 원**")
  with r6_c3:
    tax_note = st.text_input(
        "법인세 비고 입력",
        value=st.session_state.tax_note,
        label_visibility="collapsed",
    )

  initial_op_cost = (
      labor_cost
      + severance_pay
      + depreciation
      + maintenance_cost_1st_year
      + land_rent_cost
      + corporate_tax
  )
  st.success(
      f"💰 **1년 차 총 운영비 합계 (대부료 및 법인세 포함):** {initial_op_cost:,.0f} 원"
  )

# ---------------------------------------------------------
# 공통 계산 엔진 (Sheet 3 연도별 분석)
# ---------------------------------------------------------
cash_flows = [-investment]
analysis_data = []

cum_cf = -investment
cum_dcf = -investment

for year in range(0, int(years) + 1):
  if year == 0:
    analysis_data.append([
        0,
        0,
        price_per_kwh,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        -investment,
        1.0,
        -investment,
        -investment,
        -investment,
    ])
  else:
    gen = first_year_gen * ((1 - degradation) ** (year - 1))
    revenue = gen * price_per_kwh

    inflation_factor = (1 + inflation_rate) ** (year - 1)
    labor = labor_cost * inflation_factor
    severance = severance_pay * inflation_factor
    maint = maintenance_cost_1st_year * inflation_factor
    land_rent = total_land_rent * inflation_factor

    cash_op_cost = labor + severance + maint + land_rent
    dep = depreciation

    taxable_income = revenue - cash_op_cost - dep

    if taxable_income > 0:
      if taxable_income <= 200000000:
        tax = taxable_income * 0.09
      else:
        tax = 200000000 * 0.09 + (taxable_income - 200000000) * 0.19
    else:
      tax = 0

    project_cf = revenue - cash_op_cost - tax
    discount_factor = 1 / ((1 + discount_rate) ** year)
    dcf = project_cf * discount_factor

    cum_cf += project_cf
    cum_dcf += dcf
    cash_flows.append(project_cf)

    analysis_data.append([
        year,
        gen,
        price_per_kwh,
        revenue,
        labor,
        severance,
        maint,
        land_rent,
        cash_op_cost,
        dep,
        taxable_income,
        tax,
        project_cf,
        discount_factor,
        dcf,
        cum_cf,
        cum_dcf,
    ])

df_sheet3 = pd.DataFrame(
    analysis_data,
    columns=[
        "연도",
        "발전량(kWh)",
        "판매단가(원/kWh)",
        "매출액(원)",
        "인건비(원)",
        "퇴직금(원)",
        "수선유지비(원)",
        "도유지 대부료(원)",
        "현금운영비(원)",
        "감가상각비(원)",
        "과세표준(영업이익, 원)",
        "법인세(누진세율, 원)",
        "프로젝트 현금흐름(원)",
        "할인계수",
        "현금흐름 현재가치(원)",
        "누적 현금흐름(원)",
        "누적 할인현금흐름(원)",
    ],
)

npv = npf.npv(discount_rate, cash_flows)
irr = npf.irr(cash_flows) * 100 if npf.irr(cash_flows) else 0
pv_of_future_cf = npv + investment
pi = pv_of_future_cf / investment if investment > 0 else 0


# 회수기간 및 회수년도 매핑 함수
def get_payback_info(df, cf_col, cum_col):
  pos_mask = df[cum_col] > 0
  if not pos_mask.any():
    return None, None
  idx = pos_mask.idxmax()
  if idx == 0:
    return 0.0, 0
  prev_cum = df.loc[idx - 1, cum_col]
  curr_cf = df.loc[idx, cf_col]
  payback_val = df.loc[idx - 1, "연도"] + (abs(prev_cum) / curr_cf)
  payback_year = int(df.loc[idx, "연도"])
  return payback_val, payback_year


simple_payback, simple_payback_year = get_payback_info(
    df_sheet3, "프로젝트 현금흐름(원)", "누적 현금흐름(원)"
)
discounted_payback, discounted_payback_year = get_payback_info(
    df_sheet3, "현금흐름 현재가치(원)", "누적 할인현금흐름(원)"
)

# 테이블용 연도별 회수기간 컬럼 추가
simple_pb_list = []
discounted_pb_list = []

for y in df_sheet3["연도"]:
  if simple_payback_year is not None and y == simple_payback_year:
    simple_pb_list.append(f"{simple_payback:.2f}년")
  else:
    simple_pb_list.append("-")

  if discounted_payback_year is not None and y == discounted_payback_year:
    discounted_pb_list.append(f"{discounted_payback:.2f}년")
  else:
    discounted_pb_list.append("-")

df_sheet3["단순 회수기간(년)"] = simple_pb_list
df_sheet3["할인 회수기간(년)"] = discounted_pb_list

# ---------------------------------------------------------
# 테이블 맨 밑 합계 행 산정 및 연결
# ---------------------------------------------------------
df_display = df_sheet3.copy()

sum_cols = [
    "발전량(kWh)",
    "매출액(원)",
    "인건비(원)",
    "퇴직금(원)",
    "수선유지비(원)",
    "도유지 대부료(원)",
    "현금운영비(원)",
    "감가상각비(원)",
    "과세표준(영업이익, 원)",
    "법인세(누진세율, 원)",
    "프로젝트 현금흐름(원)",
    "현금흐름 현재가치(원)",
]

sum_row = {col: "" for col in df_display.columns}
sum_row["연도"] = "합계"

for col in sum_cols:
  sum_row[col] = df_display[df_display["연도"] != 0][col].sum()

df_display = pd.concat([df_display, pd.DataFrame([sum_row])], ignore_index=True)

# ---------------------------------------------------------
# Tab 3: 연도별 분석 (Sheet 3 연동 대시보드)
# ---------------------------------------------------------
with tab3:
  st.subheader("📊 연도별 분석 대시보드 (Sheet 3 구조 연동)")
  title_name = project_name if project_name else "사업명 미입력"
  title_loc = location if location else "위치 미입력"
  st.markdown(f"### 📍 {title_name} ({title_loc})")
  st.caption(
      "세후 프로젝트 현금흐름: 매출액 - 현금운영비(대부료 포함) - 법인세 (감가상각비는"
      " 과세표준 산정에 반영)"
  )
  st.divider()

  st.subheader("💡 핵심 재무 지표 요약")
  col1, col2, col3, col4, col5 = st.columns(5)
  npv_millions = npv / 1_000_000

  col1.metric("NPV (순현재가치)", f"{npv_millions:,.0f} 백만원")
  col2.metric("IRR (내부수익률)", f"{irr:.2f} %")
  col3.metric("PI (수익성지수)", f"{pi:.3f}")
  col4.metric(
      "단순 회수기간",
      (
          f"{simple_payback:.2f} 년"
          if simple_payback is not None
          else "회수 불가"
      ),
  )
  col5.metric(
      "할인 회수기간",
      (
          f"{discounted_payback:.2f} 년"
          if discounted_payback is not None
          else "회수 불가"
      ),
  )

  st.divider()
  st.subheader("📋 연도별 현금흐름 분석 상세 테이블")

  def format_cell(val, fmt="{:,.0f}"):
    if isinstance(val, (int, float)) and not pd.isna(val):
      return fmt.format(val)
    return str(val) if not pd.isna(val) else ""

  st.dataframe(
      df_display.style.format({
          "발전량(kWh)": lambda x: format_cell(x, "{:,.0f}"),
          "판매단가(원/kWh)": lambda x: format_cell(x, "{:,.1f}"),
          "매출액(원)": lambda x: format_cell(x, "{:,.0f}"),
          "인건비(원)": lambda x: format_cell(x, "{:,.0f}"),
          "퇴직금(원)": lambda x: format_cell(x, "{:,.0f}"),
          "수선유지비(원)": lambda x: format_cell(x, "{:,.0f}"),
          "도유지 대부료(원)": lambda x: format_cell(x, "{:,.0f}"),
          "현금운영비(원)": lambda x: format_cell(x, "{:,.0f}"),
          "감가상각비(원)": lambda x: format_cell(x, "{:,.0f}"),
          "과세표준(영업이익, 원)": lambda x: format_cell(x, "{:,.0f}"),
          "법인세(누진세율, 원)": lambda x: format_cell(x, "{:,.0f}"),
          "프로젝트 현금흐름(원)": lambda x: format_cell(x, "{:,.0f}"),
          "할인계수": lambda x: format_cell(x, "{:,.4f}"),
          "현금흐름 현재가치(원)": lambda x: format_cell(x, "{:,.0f}"),
          "누적 현금흐름(원)": lambda x: format_cell(x, "{:,.0f}"),
          "누적 할인현금흐름(원)": lambda x: format_cell(x, "{:,.0f}"),
      }),
      use_container_width=True,
  )

# ---------------------------------------------------------
# 페이지 2: 수익·지출·순수익 시각화 대시보드 (사이드바 메뉴)
# ---------------------------------------------------------
if page == "2. 수익·지출·순수익 시각화":
  st.title("📊 수익 · 지출 · 순수익 한눈에 보기")
  st.markdown(
      "매년 발생하는 발전 수익, 현금운영비, 법인세 및 세후 프로젝트 현금흐름 흐름을"
      " 시각적으로 비교합니다."
  )
  st.divider()

  df_chart = df_sheet3[df_sheet3["연도"] > 0].copy()
  df_melted = df_chart.melt(
      id_vars=["연도"],
      value_vars=[
          "매출액(원)",
          "현금운영비(원)",
          "법인세(누진세율, 원)",
          "프로젝트 현금흐름(원)",
      ],
      var_name="구분",
      value_name="금액(원)",
  )

  fig = px.bar(
      df_melted,
      x="연도",
      y="금액(원)",
      color="구분",
      barmode="group",
      title="연도별 매출액, 현금운영비, 법인세 및 프로젝트 현금흐름 비교",
  )
  fig.update_layout(
      xaxis_title="운영 연도", yaxis_title="금액 (원)", legend_title="항목"
  )
  st.plotly_chart(fig, use_container_width=True)

  st.divider()
  st.subheader("📈 프로젝트 현금흐름 및 누적 현금흐름 추이")
  fig_line = px.line(
      df_chart,
      x="연도",
      y=["프로젝트 현금흐름(원)", "누적 현금흐름(원)"],
      markers=True,
      title="연도별 프로젝트 현금흐름 및 누적 현금흐름 추이",
  )
  fig_line.update_layout(
      xaxis_title="운영 연도", yaxis_title="금액 (원)", legend_title="지표"
  )
  st.plotly_chart(fig_line, use_container_width=True)
