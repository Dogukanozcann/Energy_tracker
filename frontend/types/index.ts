// ---- API Response Types ----

export interface User {
  id: string
  email: string
  full_name: string
  company_name: string | null
  user_type: string
  role: string
  is_active: boolean
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface Facility {
  id: string
  user_id: string
  name: string
  description: string | null
  facility_type: string
  city: string | null
  district: string | null
  country: string
  area_sqm: number | null
  num_occupants: number | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface FacilityListResponse {
  items: Facility[]
  total: number
}

export interface EnergyConsumption {
  id: string
  facility_id: string
  energy_source_id: string
  recorded_at: string
  consumption_value: number
  unit: string
  cost: number | null
  source: string
  consumption_type: string
  is_estimated: boolean
  notes: string | null
  created_at: string
}

export interface EnergyConsumptionListResponse {
  items: EnergyConsumption[]
  total: number
  total_value: number | null
  total_cost: number | null
}

export interface CarbonFootprintItem {
  id: string
  energy_consumption_id: string
  energy_source_id: string
  scope: string
  consumption_amount: number
  consumption_unit: string
  co2_factor_used: number
  calculated_co2_kg: number
  factor_source: string | null
  calculated_at: string
}

export interface CarbonFootprint {
  id: string
  facility_id: string
  calculation_start: string
  calculation_end: string
  calculation_year: number
  calculation_month: number | null
  total_co2_kg: number
  scope_1_co2_kg: number | null
  scope_2_co2_kg: number | null
  scope_3_co2_kg: number | null
  intensity_per_area: number | null
  methodology: string
  status: string
}

export interface CarbonFootprintListResponse {
  items: CarbonFootprint[]
  total: number
}

export interface Alert {
  id: string
  facility_id: string
  energy_consumption_id: string | null
  energy_source_id: string | null
  title: string
  description: string | null
  severity: "low" | "medium" | "high" | "critical"
  category: string
  status: "new" | "acknowledged" | "resolved" | "dismissed"
  detected_value: number | null
  expected_value: number | null
  deviation_percent: number | null
  detected_at: string
  recommendation_text: string | null
  resolved_at: string | null
  is_auto_generated: boolean
  created_at: string
}

export interface AlertListResponse {
  items: Alert[]
  total: number
  new_count: number
  critical_count: number
}

export interface BatchCalculateResponse {
  processed: number
  total_co2_kg: number
  message: string
}

export interface DetectAnomalyResponse {
  alerts_created: number
  message: string
}

export interface MessageResponse {
  message: string
}

export interface BatchImportResponse {
  created: number
  skipped: number
  errors: string[]
  message: string
}

// ---- Cost Savings ----

export interface CostSavingsResponse {
  total_consumption_cost: number
  total_production_value: number
  net_cost: number
  savings: number
}

// ---- Weekly Comparison ----

export interface WeeklyComparison {
  current_week: {
    total_co2: number
    total_cost: number
  }
  previous_week: {
    total_co2: number
    total_cost: number
  }
  change_percent: number
  is_increase: boolean
}

export interface CheckAlertsResponse {
  alerts_created: number
  notifications: number
  message: string
}

// ---- Energy Source ----

export interface EnergySource {
  id: string
  name: string
  name_tr: string | null
  category: string
  unit: string
  formula_type: string
  is_renewable: boolean
  co2_factor_scope_1: number | null
  co2_factor_scope_2: number | null
}
