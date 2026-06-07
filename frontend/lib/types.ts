// ---- Cost Savings ----

export interface ProductionSavingsItem {
  id: string
  facility_id: string
  energy_source_id: string
  energy_source_name: string
  recorded_at: string
  consumption_value: number
  unit: string
  savings_amount: number
  co2_avoided_kg: number
  tree_equivalent: number
}

export interface ProductionSavingsListResponse {
  items: ProductionSavingsItem[]
  total: number
  total_savings: number
  total_co2_avoided: number
  total_tree_equivalent: number
}

export interface SavingsSummaryResponse {
  total_production: number
  total_savings: number
  total_co2_avoided: number
  total_tree_equivalent: number
  source_breakdown: Array<{
    source_name: string
    production: number
    savings: number
    co2_avoided: number
  }>
}

export interface DailyComparisonItem {
  date: string
  production_value: number
  savings_amount: number
  co2_avoided_kg: number
  tree_equivalent: number
}

export interface DailyComparisonResponse {
  items: DailyComparisonItem[]
}

// ---- Weekly Comparison ----

export interface SourceComparison {
  energy_source_id: string
  energy_source_name: string
  current_week_value: number
  previous_week_value: number
  change_pct: number
  unit: string
}

export interface WeeklyComparisonResponse {
  facility_id: string
  current_week_label: string
  previous_week_label: string
  current_week_total: number
  previous_week_total: number
  total_change_pct: number
  sources: SourceComparison[]
}

export interface SourceComparisonDetail extends SourceComparison {
  created_alerts: number
}

export interface WeeklyAlertResponse {
  compared: WeeklyComparisonResponse
  alerts_created: number
  source_details: SourceComparisonDetail[]
}
