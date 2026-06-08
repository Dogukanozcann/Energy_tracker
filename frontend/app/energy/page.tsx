"use client"

import { useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import { Zap, Calendar, Filter, Upload, Plus, X } from "lucide-react"
import { facilityApi, consumptionApi, sourceApi } from "@/lib/api"
import { Card } from "@/components/ui/Card"
import { Button } from "@/components/ui/Button"
import { ConsumptionChart } from "@/components/charts/ConsumptionChart"
import { CsvUpload } from "@/components/upload/CsvUpload"
import { formatNumber, formatDateTime } from "@/lib/utils"
import type { Facility, EnergyConsumptionListResponse, EnergySource } from "@/types"

export default function EnergyPage() {
  const searchParams = useSearchParams()
  const [facilities, setFacilities] = useState<Facility[]>([])
  const [sources, setSources] = useState<EnergySource[]>([])
  const [selected, setSelected] = useState(searchParams.get("facility_id") || "")
  const [data, setData] = useState<EnergyConsumptionListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [showImport, setShowImport] = useState(false)

  // Manuel ekleme form state
  const [showAddForm, setShowAddForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({
    energy_source_id: "",
    recorded_at: new Date().toISOString().slice(0, 16),
    consumption_value: "",
    unit: "kWh",
    cost: "",
    consumption_type: "consumption",
    notes: "",
  })

  useEffect(() => {
    Promise.all([
      facilityApi.list(),
      sourceApi.list(),
    ]).then(([facRes, srcRes]) => {
      setFacilities(facRes.items)
      setSources(srcRes)
      if (!selected && facRes.items.length > 0) {
        setSelected(facRes.items[0].id)
      }
      setLoading(false)
    })
  }, [])

  useEffect(() => {
    if (!selected) return
    setLoading(true)
    consumptionApi.list(selected, { limit: 50 })
      .then(setData)
      .finally(() => setLoading(false))
  }, [selected])

  // Kaynak seçilince birimi otomatik doldur
  useEffect(() => {
    const src = sources.find((s) => s.id === form.energy_source_id)
    if (src) setForm((f) => ({ ...f, unit: src.unit }))
  }, [form.energy_source_id, sources])

  const handleAddSubmit = async () => {
    if (!selected || !form.energy_source_id || !form.consumption_value || !form.recorded_at) return
    setSaving(true)
    try {
      await consumptionApi.create({
        facility_id: selected,
        energy_source_id: form.energy_source_id,
        recorded_at: new Date(form.recorded_at).toISOString(),
        consumption_value: Number(form.consumption_value),
        unit: form.unit,
        cost: form.cost ? Number(form.cost) : null,
        consumption_type: form.consumption_type,
        notes: form.notes || null,
      })
      setShowAddForm(false)
      setForm({
        energy_source_id: "",
        recorded_at: new Date().toISOString().slice(0, 16),
        consumption_value: "",
        unit: "kWh",
        cost: "",
        consumption_type: "consumption",
        notes: "",
      })
      // Refresh list
      consumptionApi.list(selected, { limit: 50 }).then(setData)
    } finally {
      setSaving(false)
    }
  }

  const chartData = (data?.items ?? []).map((item) => ({
    label: formatDateTime(item.recorded_at).slice(0, 16),
    value: item.consumption_value,
  })).reverse()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Enerji Tüketimi</h1>
          <p className="text-sm text-gray-500 mt-1">Anlık ve geçmiş tüketim verileri</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            {facilities.map((f) => (
              <option key={f.id} value={f.id}>{f.name}</option>
            ))}
          </select>
          <Button variant="primary" size="sm" onClick={() => setShowAddForm(true)}>
            <Plus className="w-4 h-4" />
            Manuel Ekle
          </Button>
          <Button variant="secondary" size="sm" onClick={() => setShowImport(!showImport)}>
            <Upload className="w-4 h-4" />
            CSV Yükle
          </Button>
        </div>
      </div>

      {/* Manual Entry Form */}
      {showAddForm && selected && (
        <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900">Manuel Tüketim Ekle</h2>
              <button onClick={() => setShowAddForm(false)} className="p-1 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>
            <div className="px-6 py-4 space-y-4">
              {/* Enerji Kaynağı */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Enerji Kaynağı *</label>
                <select
                  value={form.energy_source_id}
                  onChange={(e) => setForm({ ...form, energy_source_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="">Seçin...</option>
                  {sources.map((s) => (
                    <option key={s.id} value={s.id}>{s.name_tr || s.name}</option>
                  ))}
                </select>
              </div>

              {/* Tarih */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tarih & Saat *</label>
                <input
                  type="datetime-local"
                  value={form.recorded_at}
                  onChange={(e) => setForm({ ...form, recorded_at: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              {/* Değer ve Birim */}
              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tüketim Değeri *</label>
                  <input
                    type="number" step="any" min="0"
                    value={form.consumption_value}
                    onChange={(e) => setForm({ ...form, consumption_value: e.target.value })}
                    placeholder="0.00"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Birim</label>
                  <input
                    value={form.unit}
                    onChange={(e) => setForm({ ...form, unit: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              </div>

              {/* Maliyet */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Maliyet (₺) — isteğe bağlı</label>
                <input
                  type="number" step="any" min="0"
                  value={form.cost}
                  onChange={(e) => setForm({ ...form, cost: e.target.value })}
                  placeholder="0.00"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              {/* Tip */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tüketim Tipi</label>
                <select
                  value={form.consumption_type}
                  onChange={(e) => setForm({ ...form, consumption_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="consumption">Tüketim</option>
                  <option value="production">Üretim</option>
                </select>
              </div>

              {/* Notlar */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notlar</label>
                <textarea
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  rows={2}
                  placeholder="İsteğe bağlı not ekleyin..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
              <Button variant="secondary" onClick={() => setShowAddForm(false)}>İptal</Button>
              <Button
                onClick={handleAddSubmit}
                disabled={saving || !form.energy_source_id || !form.consumption_value || !form.recorded_at}
              >
                {saving ? "Kaydediliyor..." : "Kaydet"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* CSV Import */}
      {showImport && selected && (
        <CsvUpload
          facilityId={selected}
          onSuccess={() => {
            setShowImport(false)
            consumptionApi.list(selected, { limit: 50 }).then(setData)
          }}
        />
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600" />
        </div>
      ) : !selected ? (
        <Card>
          <div className="text-center py-12 text-gray-400">
            <Zap className="w-12 h-12 mx-auto mb-3" />
            <p>Lütfen bir tesis seçin</p>
          </div>
        </Card>
      ) : !data || data.items.length === 0 ? (
        <Card>
          <div className="text-center py-12 text-gray-400">
            <Zap className="w-12 h-12 mx-auto mb-3" />
            <p>Henüz tüketim verisi bulunmuyor</p>
          </div>
        </Card>
      ) : (
        <>
          {/* Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Card>
              <p className="text-xs text-gray-500 uppercase tracking-wider">Toplam Tüketim</p>
              <p className="text-xl font-bold text-gray-900 mt-1">
                {formatNumber(data.total_value ?? 0)} {data.items[0]?.unit || "kWh"}
              </p>
            </Card>
            <Card>
              <p className="text-xs text-gray-500 uppercase tracking-wider">Toplam Maliyet</p>
              <p className="text-xl font-bold text-gray-900 mt-1">
                {data.total_cost != null ? `${formatNumber(data.total_cost, 2)} ₺` : "—"}
              </p>
            </Card>
            <Card>
              <p className="text-xs text-gray-500 uppercase tracking-wider">Kayıt Sayısı</p>
              <p className="text-xl font-bold text-gray-900 mt-1">{data.total}</p>
            </Card>
            <Card>
              <p className="text-xs text-gray-500 uppercase tracking-wider">Birim</p>
              <p className="text-xl font-bold text-gray-900 mt-1">{data.items[0]?.unit || "kWh"}</p>
            </Card>
          </div>

          {/* Chart */}
          <Card title="Tüketim Grafiği">
            <ConsumptionChart data={chartData} unit={data.items[0]?.unit || "kWh"} />
          </Card>

          {/* Table */}
          <Card title="Tüketim Kayıtları">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-2 font-medium text-gray-500">Tarih</th>
                    <th className="text-right py-3 px-2 font-medium text-gray-500">Değer</th>
                    <th className="text-right py-3 px-2 font-medium text-gray-500">Maliyet</th>
                    <th className="text-center py-3 px-2 font-medium text-gray-500">Kaynak</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.slice(0, 20).map((item) => (
                    <tr key={item.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-3 px-2 text-gray-700">{formatDateTime(item.recorded_at)}</td>
                      <td className="py-3 px-2 text-right font-medium">
                        {formatNumber(item.consumption_value)} {item.unit}
                      </td>
                      <td className="py-3 px-2 text-right text-gray-500">
                        {item.cost != null ? `${formatNumber(item.cost, 2)} ₺` : "—"}
                      </td>
                      <td className="py-3 px-2 text-center">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600 capitalize">
                          {item.source}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
