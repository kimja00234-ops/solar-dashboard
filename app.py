# ---------------------------------------------------------
# Tab 1 및 Tab 3 연동용 법인세 계산 로직 (일치화)
# ---------------------------------------------------------
# 1년 차 현금운영비 + 감가상각비 합계
total_deductible_expenses = (
    labor_cost
    + auto_severance
    + depreciation
    + maintenance_cost_1st_year
    + land_rent_cost
)

# 1년 차 정확한 과세표준 (영업이익)
first_year_taxable_income = first_year_revenue - total_deductible_expenses

# 누진세율 적용 법인세 산정 (2억 이하 9%, 초과 19%)
if first_year_taxable_income > 0:
  if first_year_taxable_income <= 200000000:
    calculated_tax = int(first_year_taxable_income * 0.09)
  else:
    calculated_tax = int(
        200000000 * 0.09 + (first_year_taxable_income - 200000000) * 0.19
    )
else:
  calculated_tax = 0
