"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import {
  Building2,
  Zap,
  Leaf,
  Bell,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
  RefreshCw,
  Upload,
  Filter,
  X,
  Calendar,
} from "lucide-react"
import { useAuth } from "@/lib/auth"
import { Card } from "@/components/ui/Card"
import { Badge } from "@/components/ui/Badge"
import { Button } from "@/components/ui/Button"
import { ConsumptionChart } from "@/components/charts/ConsumptionChart"
import { facilityApi, consumptionApi, carbonApi, alertApi, reportApi, savingsApi, comparisonApi, sourceApi } from "@/lib/api"
import { formatNumber, formatCO2, formatDateTime, getSeverityColor, toLocalISOString } from "@/lib/utils"
import type { Facility, EnergyConsumptionListResponse, CarbonFootprintListResponse, AlertListResponse, EnergySource } from "@/types"
import type { SavingsSummaryResponse, WeeklyComparisonResponse } from "@/lib/types"

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  color,
}: {
  icon: any
  label: string
  value: string
  sub?: string
  color: string
}) {
  return (
    <div className="bg-white/90 backdrop-blur-sm rounded-xl border border-gray-200/80 p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <div className={`p-2.5 rounded-lg ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="min-w-0">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">{label}</p>
          <p className="text-xl font-bold text-gray-900 mt-0.5">{value}</p>
          {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
        </div>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const router = useRouter()
  const { user } = useAuth()
  const [facilities, setFacilities] = useState<Facility[]>([])
  const [selectedFacility, setSelectedFacility] = useState<string>("")
  const [sources, setSources] = useState<EnergySource[]>([])
  const [consumption, setConsumption] = useState<EnergyConsumptionListResponse | null>(null)
  const [footprint, setFootprint] = useState<CarbonFootprintListResponse | null>(null)
  const [alerts, setAlerts] = useState<AlertListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [calculating, setCalculating] = useState(false)
  const [calcMessage, setCalcMessage] = useState<string | null>(null)
  const [batchResult, setBatchResult] = useState<{ count: number; total_kg: number } | null>(null)
  const [savingsSummary, setSavingsSummary] = useState<SavingsSummaryResponse | null>(null)
  const [weeklyComparison, setWeeklyComparison] = useState<WeeklyComparisonResponse | null>(null)

  // Filter state
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [selectedSourceId, setSelectedSourceId] = useState("")
  const [consumptionType, setConsumptionType] = useState("")
  const [filtersActive, setFiltersActive] = useState(false)

  const hasFilters = dateFrom || dateTo || selectedSourceId || consumptionType

  const fetchData = useCallback(async () => {
    if (!selectedFacility) return
    setLoading(true)

    const params: Record<string, any> = {}
    if (dateFrom) params.date_from = `${dateFrom}T00:00:00`
    if (dateTo) params.date_to = `${dateTo}T23:59:59`
    if (selectedSourceId) params.energy_source_id = selectedSourceId
    if (consumptionType) params.consumption_type = consumptionType
    if (!hasFilters) params.limit = 10

    Promise.all([
      consumptionApi.list(selectedFacility, params),
      carbonApi.footprints(selectedFacility),
      alertApi.list(selectedFacility, { limit: 5 }),
      savingsApi.summary(selectedFacility).catch(() => null),
      comparisonApi.weekly(selectedFacility).catch(() => null),
    ])
      .then(([c, f, a, s, w]) => {
        setConsumption(c)
        setFootprint(f)
        setAlerts(a)
        setSavingsSummary(s)
        setWeeklyComparison(w)
      })
      .finally(() => {
        setLoading(false)
        // batchResult'i temizle — yeni filtreler eski hesaplama sonucunu göstermesin
        setBatchResult(null)
      })
  }, [selectedFacility, dateFrom, dateTo, selectedSourceId, consumptionType, hasFilters])

  // Load facilities & sources on mount
  useEffect(() => {
    Promise.all([
      facilityApi.list(),
      sourceApi.list(),
    ]).then(([facRes, srcRes]) => {
      setFacilities(facRes.items)
      setSources(srcRes)
      if (facRes.items.length > 0) {
        setSelectedFacility(facRes.items[0].id)
      }
      setLoading(false)
    })
  }, [])

  // Fetch data when facility or filters change
  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleApplyFilters = () => {
    setFiltersActive(true)
    // fetchData will be triggered by state change
  }

  const handleResetFilters = () => {
    setDateFrom("")
    setDateTo("")
    setSelectedSourceId("")
    setConsumptionType("")
    setFiltersActive(false)
  }

  const handleCalculate = async () => {
    if (!selectedFacility) return
    setCalculating(true)
    setCalcMessage(null)
    try {
      // 1. Tarih filtrelerini ISO datetime'a çevir (input type="date" yyyy-MM-dd verir)
      const dateFromISO = dateFrom ? `${dateFrom}T00:00:00` : undefined
      const dateToISO = dateTo ? `${dateTo}T23:59:59` : undefined
      const batchRes = await carbonApi.calculateBatch(
        selectedFacility,
        false,
        dateFromISO,
        dateToISO,
      )

      // 2. Eğer tarih aralığı seçiliyse footprint oluşturma — kullanıcı dashboard'da
      //    filtrelediği aralığın karbon hesabını görsün istiyor. Batch calculate zaten
      //    CarbonFootprintItem'ları oluşturur. Yıllık/aylık footprint oluşturmak yerine
      //    doğrudan batch sonucunu göster.
      if (!dateFrom && !dateTo) {
        // Tarih filtresi yoksa yıllık footprint oluştur (eski davranış)
        const currentYear = new Date().getFullYear()
        await carbonApi.generateFootprint(selectedFacility, currentYear).catch(() => {})
      }

      // Batch sonucunu state'e kaydet (dashboard'da göstermek için)
      setBatchResult({
        count: batchRes.processed,
        total_kg: batchRes.total_co2_kg,
      })
      setCalcMessage(batchRes.message || "Karbon hesaplaması tamamlandı.")

      // 3. Yenile (ISO datetime formatı kullan)
      const refreshDateFrom = dateFrom ? `${dateFrom}T00:00:00` : undefined
      const refreshDateTo = dateTo ? `${dateTo}T23:59:59` : undefined
      const [c, f] = await Promise.all([
        consumptionApi.list(selectedFacility, hasFilters ? { date_from: refreshDateFrom, date_to: refreshDateTo, energy_source_id: selectedSourceId, consumption_type: consumptionType } : { limit: 10 }),
        carbonApi.footprints(selectedFacility),
      ])
      setConsumption(c)
      setFootprint(f)
    } catch (err: any) {
      setCalcMessage(err?.message || "Hesaplama sırasında hata oluştu.")
    } finally {
      setCalculating(false)
    }
  }

  // Chart data
  const chartData =
    consumption?.items.map((item) => ({
      label: formatDateTime(item.recorded_at).slice(0, 16),
      value: item.consumption_value,
    })) ?? []

  const totalConsumption = consumption?.total_value ?? 0
  const latestFootprint = footprint?.items?.[0]
  const alertItems = alerts?.items ?? []
  const chartTitle = hasFilters
    ? `Enerji Tüketimi (${consumption?.items.length ?? 0} kayıt)`
    : "Enerji Tüketimi (Son 10 Kayıt)"

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">
            Hoş geldiniz, {user?.full_name}
          </p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          <select
            value={selectedFacility}
            onChange={(e) => setSelectedFacility(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            {facilities.length === 0 && <option value="">Tesis seçin</option>}
            {facilities.map((f) => (
              <option key={f.id} value={f.id}>
                {f.name}
              </option>
            ))}
          </select>
          <Button variant="secondary" size="sm" onClick={handleCalculate} disabled={calculating}>
            <RefreshCw className={`w-4 h-4 ${calculating ? "animate-spin" : ""}`} />
            Karbon Hesapla
          </Button>
          {selectedFacility && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                const win = window.open("", "_blank")
                if (win) {
                  reportApi.carbonHtml(selectedFacility).then((res) => {
                    res.text().then((html) => {
                      win.document.write(html)
                      win.document.close()
                    })
                  })
                }
              }}
            >
              <Upload className="w-4 h-4" />
              Rapor İndir
            </Button>
          )}
        </div>
      </div>

      {/* Calculation message */}
      {calcMessage && (
        <div className="bg-green-50 border border-green-200 text-green-800 text-sm px-4 py-3 rounded-lg flex items-center justify-between">
          <span>{calcMessage}</span>
          <button onClick={() => setCalcMessage(null)} className="text-green-600 hover:text-green-800">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Tesis yoksa uyarı */}
      {facilities.length === 0 && !loading && (
        <Card>
          <div className="text-center py-8">
            <Building2 className="w-12 h-12 text-gray-300 mx-auto" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">Henüz tesis eklenmemiş</h3>
            <p className="mt-1 text-sm text-gray-500">
              Enerji takibine başlamak için ilk tesisinizi ekleyin.
            </p>
            <Button className="mt-4" onClick={() => router.push("/facilities")}>
              Tesis Ekle
            </Button>
          </div>
        </Card>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600" />
        </div>
      ) : facilities.length > 0 ? (
        <>
          {/* Filter Bar */}
          <div className="bg-white/80 backdrop-blur-sm rounded-xl border border-gray-200/80 p-4 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <Filter className="w-4 h-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-700">Filtreler</span>
              {hasFilters && (
                <span className="text-xs bg-brand-100 text-brand-700 px-2 py-0.5 rounded-full">
                  Aktif
                </span>
              )}
            </div>
            <div className="flex flex-wrap items-end gap-3">
              {/* Date From */}
              <div className="flex-1 min-w-[140px]">
                <label className="block text-xs font-medium text-gray-500 mb-1">Başlangıç</label>
                <div className="relative">
                  <Calendar className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="date"
                    value={dateFrom}
                    onChange={(e) => setDateFrom(e.target.value)}
                    className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              </div>

              {/* Date To */}
              <div className="flex-1 min-w-[140px]">
                <label className="block text-xs font-medium text-gray-500 mb-1">Bitiş</label>
                <div className="relative">
                  <Calendar className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="date"
                    value={dateTo}
                    onChange={(e) => setDateTo(e.target.value)}
                    className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              </div>

              {/* Energy Source */}
              <div className="flex-1 min-w-[140px]">
                <label className="block text-xs font-medium text-gray-500 mb-1">Enerji Kaynağı</label>
                <select
                  value={selectedSourceId}
                  onChange={(e) => setSelectedSourceId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="">Tümü</option>
                  {sources.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name_tr || s.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Consumption Type */}
              <div className="flex-1 min-w-[120px]">
                <label className="block text-xs font-medium text-gray-500 mb-1">Tüketim Tipi</label>
                <select
                  value={consumptionType}
                  onChange={(e) => setConsumptionType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="">Tümü</option>
                  <option value="consumption">Tüketim</option>
                  <option value="production">Üretim</option>
                </select>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2">
                <Button size="sm" onClick={handleApplyFilters}>
                  <Filter className="w-4 h-4" />
                  Uygula
                </Button>
                {hasFilters && (
                  <Button variant="ghost" size="sm" onClick={handleResetFilters}>
                    <X className="w-4 h-4" />
                    Sıfırla
                  </Button>
                )}
              </div>
            </div>
          </div>

          {/* Stat Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              icon={Zap}
              label="Toplam Tüketim"
              value={`${formatNumber(totalConsumption)} ${consumption?.items?.[0]?.unit || "kWh"}`}
              sub={hasFilters ? "Filtrelenmiş" : "Seçili tesiste"}
              color="bg-yellow-50 text-yellow-600"
            />
            <StatCard
              icon={Leaf}
              label={hasFilters && batchResult ? "Karbon (Filtre)" : "Karbon Ayak İzi"}
              value={hasFilters && batchResult ? formatCO2(batchResult.total_kg) : formatCO2(latestFootprint?.total_co2_kg ?? 0)}
              sub={hasFilters && batchResult ? `${batchResult.count} kayıt işlendi` : (latestFootprint ? `${latestFootprint.calculation_year} yılı` : "Henüz hesaplanmamış")}
              color="bg-green-50 text-green-600"
            />
            <StatCard
              icon={Bell}
              label="Aktif Uyarılar"
              value={String(alerts?.new_count ?? 0)}
              sub={alerts?.critical_count ? `${alerts.critical_count} kritik` : "Temiz"}
              color="bg-red-50 text-red-600"
            />
            <StatCard
              icon={Building2}
              label="Tesis Sayısı"
              value={String(facilities.length)}
              sub={facilities.map((f) => f.name).join(", ")}
              color="bg-blue-50 text-blue-600"
            />
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Consumption Chart */}
            <div className="lg:col-span-2">
              <Card title={chartTitle}>
                <ConsumptionChart data={chartData} unit={consumption?.items?.[0]?.unit || "kWh"} />
              </Card>
            </div>

            {/* Carbon Summary */}
            <div>
              <Card title={hasFilters ? "Karbon (Filtrelenmiş)" : "Karbon Özeti"}>
                {hasFilters && batchResult && batchResult.count > 0 ? (
                  <div className="space-y-4">
                    <div className="text-center">
                      <p className="text-3xl font-bold text-gray-900">
                        {formatCO2(batchResult.total_kg)}
                      </p>
                      <p className="text-sm text-gray-500">
                        {dateFrom && dateTo
                          ? `${dateFrom} → ${dateTo}`
                          : "Seçili aralık"}
                      </p>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">İşlenen kayıt</span>
                        <span className="font-medium">{batchResult.count}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Ortalama CO₂/kayıt</span>
                        <span className="font-medium">
                          {formatCO2(batchResult.total_kg / batchResult.count)}
                        </span>
                      </div>
                    </div>
                  </div>
                ) : latestFootprint ? (
                  <div className="space-y-4">
                    <div className="text-center">
                      <p className="text-3xl font-bold text-gray-900">
                        {formatCO2(latestFootprint.total_co2_kg)}
                      </p>
                      <p className="text-sm text-gray-500">
                        {latestFootprint.calculation_month
                          ? `${latestFootprint.calculation_year}/${String(latestFootprint.calculation_month).padStart(2, "0")}`
                          : `${latestFootprint.calculation_year}`}
                      </p>
                    </div>
                    <div className="space-y-2">
                      {[
                        { label: "Scope 1 (Doğrudan)", value: latestFootprint.scope_1_co2_kg },
                        { label: "Scope 2 (Elektrik)", value: latestFootprint.scope_2_co2_kg },
                        { label: "Scope 3 (Diğer)", value: latestFootprint.scope_3_co2_kg },
                      ].map((item) => (
                        <div key={item.label} className="flex justify-between text-sm">
                          <span className="text-gray-500">{item.label}</span>
                          <span className="font-medium">{formatCO2(item.value)}</span>
                        </div>
                      ))}
                      {latestFootprint.intensity_per_area && (
                        <div className="flex justify-between text-sm pt-2 border-t border-gray-100">
                          <span className="text-gray-500">Birim alan</span>
                          <span className="font-medium">
                            {formatNumber(latestFootprint.intensity_per_area, 2)} kg/m²
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-6 text-gray-400 text-sm">
                    Karbon hesaplaması yapılmamış.
                    <br />
                    "Karbon Hesapla" butonunu kullanın.
                  </div>
                )}
              </Card>
            </div>
          </div>

          {/* Savings & Weekly Comparison Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Cost Savings Card */}
            <Card title="Yenilenebilir Enerji Tasarrufu" subtitle={savingsSummary ? `₺${formatNumber(savingsSummary.total_savings, 0)} toplam tasarruf` : "Veri yükleniyor..."}>
              {savingsSummary ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-green-50 rounded-lg p-3 text-center">
                      <p className="text-2xl font-bold text-green-700">{formatNumber(savingsSummary.total_production, 0)}</p>
                      <p className="text-xs text-green-600">Üretim (kWh)</p>
                    </div>
                    <div className="bg-emerald-50 rounded-lg p-3 text-center">
                      <p className="text-2xl font-bold text-emerald-700">₺{formatNumber(savingsSummary.total_savings, 0)}</p>
                      <p className="text-xs text-emerald-600">Tasarruf</p>
                    </div>
                    <div className="bg-teal-50 rounded-lg p-3 text-center">
                      <p className="text-2xl font-bold text-teal-700">{formatNumber(savingsSummary.total_co2_avoided, 0)}</p>
                      <p className="text-xs text-teal-600">CO₂ (kg) önlendi</p>
                    </div>
                    <div className="bg-cyan-50 rounded-lg p-3 text-center">
                      <p className="text-2xl font-bold text-cyan-700">{formatNumber(savingsSummary.total_tree_equivalent, 0)}</p>
                      <p className="text-xs text-cyan-600">Ağaç eşdeğeri</p>
                    </div>
                  </div>
                  {savingsSummary.source_breakdown.length > 0 && (
                    <div className="space-y-1.5">
                      <p className="text-xs font-medium text-gray-500 uppercase">Kaynak Bazında</p>
                      {savingsSummary.source_breakdown.map((s) => (
                        <div key={s.source_name} className="flex justify-between text-sm">
                          <span className="text-gray-600">{s.source_name}</span>
                          <span className="font-medium">₺{formatNumber(s.savings, 0)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-6 text-gray-400 text-sm">
                  Tasarruf verisi bulunamadı.
                </div>
              )}
            </Card>

            {/* Weekly Comparison Card */}
            <Card title="Haftalık Karşılaştırma" subtitle={weeklyComparison ? `${weeklyComparison.current_week_label} vs ${weeklyComparison.previous_week_label}` : "Veri yükleniyor..."}>
              {weeklyComparison ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="text-center flex-1">
                      <p className="text-xs text-gray-500">Önceki Hafta</p>
                      <p className="text-lg font-bold text-gray-900">{formatNumber(weeklyComparison.previous_week_total, 0)}</p>
                      <p className="text-xs text-gray-400">kWh</p>
                    </div>
                    <div className="text-center flex-1">
                      <p className="text-xs text-gray-500">Bu Hafta</p>
                      <p className="text-lg font-bold text-gray-900">{formatNumber(weeklyComparison.current_week_total, 0)}</p>
                      <p className="text-xs text-gray-400">kWh</p>
                    </div>
                  </div>
                  <div className="text-center">
                    <span className={`inline-flex items-center gap-1 text-sm font-medium px-3 py-1 rounded-full ${
                      weeklyComparison.total_change_pct > 0 ? "bg-red-50 text-red-700" :
                      weeklyComparison.total_change_pct < 0 ? "bg-green-50 text-green-700" :
                      "bg-gray-50 text-gray-500"
                    }`}>
                      <TrendingUp className="w-4 h-4" />
                      %{weeklyComparison.total_change_pct > 0 ? "+" : ""}{weeklyComparison.total_change_pct.toFixed(1)}
                    </span>
                  </div>
                  {weeklyComparison.sources.length > 0 && (
                    <div className="space-y-1.5">
                      <p className="text-xs font-medium text-gray-500 uppercase">Kaynak Bazında Değişim</p>
                      {weeklyComparison.sources.map((s) => (
                        <div key={s.energy_source_id} className="flex justify-between items-center text-sm">
                          <span className="text-gray-600">{s.energy_source_name}</span>
                          <span className={`font-medium ${
                            s.change_pct > 0 ? "text-red-600" :
                            s.change_pct < 0 ? "text-green-600" :
                            "text-gray-500"
                          }`}>
                            {s.change_pct > 0 ? "+" : ""}{s.change_pct.toFixed(1)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-6 text-gray-400 text-sm">
                  Karşılaştırma verisi bulunamadı.
                </div>
              )}
            </Card>
          </div>

          {/* Alerts Row */}
          <Card
            title="Son Uyarılar"
            subtitle={alertItems.length > 0 ? undefined : "Aktif uyarı bulunmuyor"}
          >
            {alertItems.length > 0 ? (
              <div className="space-y-3">
                {alertItems.map((alert) => (
                  <div
                    key={alert.id}
                    className="flex items-start gap-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50 transition-colors"
                  >
                    <AlertTriangle className={`w-5 h-5 mt-0.5 shrink-0 ${
                      alert.severity === "critical" ? "text-red-500" :
                      alert.severity === "high" ? "text-orange-500" : "text-yellow-500"
                    }`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-gray-900 truncate">{alert.title}</p>
                        <Badge variant={
                          alert.severity === "critical" ? "danger" :
                          alert.severity === "high" ? "warning" :
                          alert.severity === "medium" ? "info" : "default"
                        }>
                          {alert.severity}
                        </Badge>
                      </div>
                      {alert.deviation_percent && (
                        <p className="text-xs text-gray-500 mt-0.5">
                          Sapma: %{Math.abs(alert.deviation_percent).toFixed(1)}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full"
                  onClick={() => router.push("/alerts")}
                >
                  Tüm Uyarılar <ArrowRight className="w-4 h-4" />
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-sm text-gray-400 py-2">
                <TrendingUp className="w-4 h-4" />
                Sistem temiz görünüyor.
              </div>
            )}
          </Card>
        </>
      ) : null}
    </div>
  )
}
