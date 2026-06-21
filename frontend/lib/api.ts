/**
 * API client — tüm backend çağrıları buradan geçer.
 * Otomatik olarak localStorage'daki token'ı Authorization header'a ekler.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1"

class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
    this.name = "ApiError"
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  }
  if (token) headers["Authorization"] = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  // 204 No Content
  if (res.status === 204) return undefined as T

  const data = await res.json()

  if (!res.ok) {
    throw new ApiError(data.detail || "Bir hata oluştu", res.status)
  }

  return data as T
}

// ---- Auth ----

export const authApi = {
  login: (email: string, password: string) =>
    request<import("../types").AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  register: (data: {
    email: string
    password: string
    full_name: string
    company_name?: string
    user_type?: string
  }) =>
    request<import("../types").AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  me: () => request<import("../types").User>("/auth/me"),

  forgotPassword: (email: string) =>
    request<import("../types").MessageResponse>("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  resetPassword: (token: string, new_password: string) =>
    request<import("../types").MessageResponse>("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, new_password }),
    }),

  verifyEmail: (token: string) =>
    request<import("../types").MessageResponse>("/auth/verify-email", {
      method: "POST",
      body: JSON.stringify({ token }),
    }),
}

// ---- Facilities ----

export const facilityApi = {
  list: (skip = 0, limit = 50) =>
    request<import("../types").FacilityListResponse>(
      `/facilities/?skip=${skip}&limit=${limit}`,
    ),

  get: (id: string) =>
    request<import("../types").Facility>(`/facilities/${id}`),

  create: (data: Partial<import("../types").Facility>) =>
    request<import("../types").Facility>("/facilities/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<import("../types").Facility>) =>
    request<import("../types").Facility>(`/facilities/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    request<void>(`/facilities/${id}`, { method: "DELETE" }),
}

// ---- Energy Consumption ----

export const consumptionApi = {
  list: (
    facilityId: string,
    params?: {
      date_from?: string
      date_to?: string
      energy_source_id?: string
      consumption_type?: string
      skip?: number
      limit?: number
    },
  ) => {
    const searchParams = new URLSearchParams({ facility_id: facilityId })
    if (params?.date_from) searchParams.set("date_from", params.date_from)
    if (params?.date_to) searchParams.set("date_to", params.date_to)
    if (params?.energy_source_id)
      searchParams.set("energy_source_id", params.energy_source_id)
    if (params?.consumption_type)
      searchParams.set("consumption_type", params.consumption_type)
    if (params?.skip) searchParams.set("skip", String(params.skip))
    if (params?.limit) searchParams.set("limit", String(params.limit))
    return request<import("../types").EnergyConsumptionListResponse>(
      `/energy-consumption/?${searchParams}`,
    )
  },

  create: (data: {
    facility_id: string
    energy_source_id: string
    recorded_at: string
    consumption_value: number
    unit?: string
    cost?: number | null
    consumption_type?: string
    notes?: string | null
  }) =>
    request<import("../types").EnergyConsumption>("/energy-consumption/", {
      method: "POST",
      body: JSON.stringify({
        ...data,
        source: "manual",
        consumption_type: data.consumption_type || "consumption",
        unit: data.unit || "kWh",
      }),
    }),

  delete: (id: string) =>
    request<void>(`/energy-consumption/${id}`, { method: "DELETE" }),
}

// ---- Imports ----

export const importApi = {
  uploadConsumption: async (facilityId: string, file: File) => {
    const token =
      typeof window !== "undefined" ? localStorage.getItem("token") : null
    const formData = new FormData()
    formData.append("file", file)
    const headers: Record<string, string> = {}
    if (token) headers["Authorization"] = `Bearer ${token}`
    const res = await fetch(
      `${API_BASE}/imports/consumption?facility_id=${facilityId}`,
      { method: "POST", body: formData, headers },
    )
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Import hatası")
    return data as import("../types").BatchImportResponse
  },
}

// ---- Reports ----

export const reportApi = {
  carbonHtml: (facilityId: string) => {
    const token =
      typeof window !== "undefined" ? localStorage.getItem("token") : null
    const headers: Record<string, string> = {}
    if (token) headers["Authorization"] = `Bearer ${token}`
    return fetch(`${API_BASE}/reports/carbon/${facilityId}`, { headers })
  },
}

// ---- Carbon ----

export const carbonApi = {
  calculateBatch: (facilityId: string, force = false, dateFrom?: string, dateTo?: string) => {
    const body: Record<string, any> = { facility_id: facilityId, force_recalculate: force }
    if (dateFrom) body.date_from = dateFrom
    if (dateTo) body.date_to = dateTo
    return request<import("../types").BatchCalculateResponse>("/carbon/calculate-batch", {
      method: "POST",
      body: JSON.stringify(body),
    })
  },

  footprints: (facilityId: string) =>
    request<import("../types").CarbonFootprintListResponse>(
      `/carbon/footprints?facility_id=${facilityId}`,
    ),

  generateFootprint: (facilityId: string, year: number, month?: number) =>
    request<import("../types").CarbonFootprint>(
      "/carbon/footprints/generate",
      {
        method: "POST",
        body: JSON.stringify({ facility_id: facilityId, year, month }),
      },
    ),
}

// ---- Alerts ----

export const alertApi = {
  list: (
    facilityId: string,
    params?: {
      status?: string
      severity?: string
      category?: string
      skip?: number
      limit?: number
    },
  ) => {
    const searchParams = new URLSearchParams({ facility_id: facilityId })
    if (params?.status) searchParams.set("status", params.status)
    if (params?.severity) searchParams.set("severity", params.severity)
    if (params?.category) searchParams.set("category", params.category)
    if (params?.skip) searchParams.set("skip", String(params.skip))
    if (params?.limit) searchParams.set("limit", String(params.limit))
    return request<import("../types").AlertListResponse>(
      `/alerts/?${searchParams}`,
    )
  },

  updateStatus: (id: string, status: string) =>
    request<import("../types").Alert>(`/alerts/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),

  detect: (facilityId: string, threshold = 20) =>
    request<import("../types").DetectAnomalyResponse>("/alerts/detect", {
      method: "POST",
      body: JSON.stringify({
        facility_id: facilityId,
        deviation_threshold: threshold,
      }),
    }),
}

// ---- Cost Savings ----

export const savingsApi = {
  list: (facilityId: string, params?: { date_from?: string; date_to?: string; skip?: number; limit?: number }) => {
    const searchParams = new URLSearchParams({ facility_id: facilityId })
    if (params?.date_from) searchParams.set("date_from", params.date_from)
    if (params?.date_to) searchParams.set("date_to", params.date_to)
    if (params?.skip) searchParams.set("skip", String(params.skip))
    if (params?.limit) searchParams.set("limit", String(params.limit))
    return request<import("../types").ProductionSavingsListResponse>(
      `/cost-savings/?${searchParams}`,
    )
  },

  summary: (facilityId: string, dateFrom?: string, dateTo?: string, energySourceId?: string, consumptionType?: string) => {
    const params = new URLSearchParams({ facility_id: facilityId })
    if (dateFrom) params.set("date_from", dateFrom)
    if (dateTo) params.set("date_to", dateTo)
    if (energySourceId) params.set("energy_source_id", energySourceId)
    if (consumptionType) params.set("consumption_type", consumptionType)
    return request<import("../types").SavingsSummaryResponse>(
      `/cost-savings/summary?${params}`,
    )
  },

  daily: (facilityId: string, dateFrom?: string, dateTo?: string) => {
    const params = new URLSearchParams({ facility_id: facilityId })
    if (dateFrom) params.set("date_from", dateFrom)
    if (dateTo) params.set("date_to", dateTo)
    return request<import("../types").DailyComparisonResponse>(
      `/cost-savings/daily?${params}`,
    )
  },
}

// ---- Weekly Comparison ----

export const comparisonApi = {
  weekly: (facilityId: string, endDate?: string, energySourceId?: string, consumptionType?: string) => {
    const params = new URLSearchParams({ facility_id: facilityId })
    if (endDate) params.set("end_date", endDate)
    if (energySourceId) params.set("energy_source_id", energySourceId)
    if (consumptionType) params.set("consumption_type", consumptionType)
    return request<import("../types").WeeklyComparisonResponse>(
      `/weekly-comparison/?${params}`,
    )
  },

  checkAlerts: (facilityId: string, threshold = 20, endDate?: string) => {
    const params = new URLSearchParams({ facility_id: facilityId, threshold_pct: String(threshold) })
    if (endDate) params.set("end_date", endDate)
    return request<import("../types").WeeklyAlertResponse>(
      `/weekly-comparison/check-alerts?${params}`,
      { method: "POST" },
    )
  },
}

// ---- Energy Sources ----

export const sourceApi = {
  list: () =>
    request<import("../types").EnergySource[]>("/energy-sources/"),
}

// ---- Admin ----

export const adminApi = {
  // Energy Sources
  listSources: () =>
    request<import("../types").EnergySourceDetail[]>("/admin/energy-sources"),

  getSource: (id: string) =>
    request<import("../types").EnergySourceDetail>(`/admin/energy-sources/${id}`),

  createSource: (data: any) =>
    request<import("../types").EnergySourceDetail>("/admin/energy-sources", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateSource: (id: string, data: any) =>
    request<import("../types").EnergySourceDetail>(`/admin/energy-sources/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deleteSource: (id: string) =>
    request<void>(`/admin/energy-sources/${id}`, { method: "DELETE" }),

  // Users
  listUsers: (skip = 0, limit = 50) =>
    request<import("../types").UserListResponse>(`/admin/users?skip=${skip}&limit=${limit}`),

  getUser: (id: string) =>
    request<import("../types").UserDetail>(`/admin/users/${id}`),

  updateUser: (id: string, data: any) =>
    request<import("../types").UserDetail>(`/admin/users/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  // System Settings
  listSettings: (category?: string) =>
    request<import("../types").SettingListResponse>(`/admin/settings${category ? `?category=${category}` : ""}`),

  getSetting: (id: string) =>
    request<import("../types").SystemSetting>(`/admin/settings/${id}`),

  createSetting: (data: any) =>
    request<import("../types").SystemSetting>("/admin/settings", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateSetting: (id: string, data: any) =>
    request<import("../types").SystemSetting>(`/admin/settings/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deleteSetting: (id: string) =>
    request<void>(`/admin/settings/${id}`, { method: "DELETE" }),

  // Audit Logs
  listLogs: (skip = 0, limit = 50) =>
    request<import("../types").LogListResponse>(`/admin/logs?skip=${skip}&limit=${limit}`),
}
