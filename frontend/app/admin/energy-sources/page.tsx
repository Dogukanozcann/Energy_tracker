"use client"

import { useEffect, useState } from "react"
import { Plus, Pencil, Trash2, X, Zap } from "lucide-react"
import { adminApi } from "@/lib/api"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"
import { Badge } from "@/components/ui/Badge"
import type { EnergySourceDetail } from "@/types"

interface FormData {
  name: string
  name_tr: string
  category: string
  unit: string
  formula_type: string
  is_renewable: boolean
  is_active: boolean
  co2_factor_scope_1: string
  co2_factor_scope_2: string
  co2_factor_source: string
  fuel_density: string
  fuel_carbon_ratio: string
  fuel_co2_per_liter: string
}

const defaultForm: FormData = {
  name: "",
  name_tr: "",
  category: "electricity",
  unit: "kWh",
  formula_type: "direct_emission",
  is_renewable: false,
  is_active: true,
  co2_factor_scope_1: "",
  co2_factor_scope_2: "",
  co2_factor_source: "",
  fuel_density: "",
  fuel_carbon_ratio: "",
  fuel_co2_per_liter: "",
}

export default function AdminEnergySourcesPage() {
  const [sources, setSources] = useState<EnergySourceDetail[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<FormData>(defaultForm)
  const [saving, setSaving] = useState(false)

  const load = () => {
    setLoading(true)
    adminApi.listSources().then(setSources).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const openCreate = () => {
    setForm(defaultForm)
    setEditingId(null)
    setShowForm(true)
  }

  const openEdit = (s: EnergySourceDetail) => {
    setForm({
      name: s.name,
      name_tr: s.name_tr || "",
      category: s.category,
      unit: s.unit,
      formula_type: s.formula_type,
      is_renewable: s.is_renewable,
      is_active: s.is_active,
      co2_factor_scope_1: s.co2_factor_scope_1?.toString() || "",
      co2_factor_scope_2: s.co2_factor_scope_2?.toString() || "",
      co2_factor_source: s.co2_factor_source || "",
      fuel_density: s.fuel_density?.toString() || "",
      fuel_carbon_ratio: s.fuel_carbon_ratio?.toString() || "",
      fuel_co2_per_liter: s.fuel_co2_per_liter?.toString() || "",
    })
    setEditingId(s.id)
    setShowForm(true)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const data = {
        ...form,
        co2_factor_scope_1: form.co2_factor_scope_1 ? Number(form.co2_factor_scope_1) : null,
        co2_factor_scope_2: form.co2_factor_scope_2 ? Number(form.co2_factor_scope_2) : null,
        fuel_density: form.fuel_density ? Number(form.fuel_density) : null,
        fuel_carbon_ratio: form.fuel_carbon_ratio ? Number(form.fuel_carbon_ratio) : null,
        fuel_co2_per_liter: form.fuel_co2_per_liter ? Number(form.fuel_co2_per_liter) : null,
      }
      if (editingId) {
        await adminApi.updateSource(editingId, data)
      } else {
        await adminApi.createSource(data)
      }
      setShowForm(false)
      load()
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`"${name}" kaynağını silmek istediğinize emin misiniz?`)) return
    await adminApi.deleteSource(id)
    load()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Enerji Kaynakları</h1>
          <p className="text-sm text-gray-500 mt-1">Tüm enerji kaynaklarını yönetin</p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="w-4 h-4" />
          Yeni Kaynak Ekle
        </Button>
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900">
                {editingId ? "Kaynağı Düzenle" : "Yeni Kaynak Ekle"}
              </h2>
              <button onClick={() => setShowForm(false)} className="p-1 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Adı *</label>
                  <input
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Türkçe Adı</label>
                  <input
                    value={form.name_tr}
                    onChange={(e) => setForm({ ...form, name_tr: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Kategori</label>
                  <select
                    value={form.category}
                    onChange={(e) => setForm({ ...form, category: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    <option value="electricity">Electricity</option>
                    <option value="natural_gas">Natural Gas</option>
                    <option value="fuel">Fuel</option>
                    <option value="renewable">Renewable</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Birim</label>
                  <input
                    value={form.unit}
                    onChange={(e) => setForm({ ...form, unit: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Formül Tipi</label>
                  <input
                    value={form.formula_type}
                    onChange={(e) => setForm({ ...form, formula_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div className="flex items-center gap-4 pt-6">
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={form.is_renewable}
                      onChange={(e) => setForm({ ...form, is_renewable: e.target.checked })}
                      className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                    />
                    Yenilenebilir
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={form.is_active}
                      onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                      className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                    />
                    Aktif
                  </label>
                </div>
              </div>
              <details className="text-sm">
                <summary className="cursor-pointer text-gray-600 font-medium">CO₂ Faktörleri & Yakıt Detayları</summary>
                <div className="grid grid-cols-2 gap-4 mt-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">CO₂ Faktörü (Scope 1)</label>
                    <input
                      type="number" step="any"
                      value={form.co2_factor_scope_1}
                      onChange={(e) => setForm({ ...form, co2_factor_scope_1: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">CO₂ Faktörü (Scope 2)</label>
                    <input
                      type="number" step="any"
                      value={form.co2_factor_scope_2}
                      onChange={(e) => setForm({ ...form, co2_factor_scope_2: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Kaynak</label>
                    <input
                      value={form.co2_factor_source}
                      onChange={(e) => setForm({ ...form, co2_factor_source: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Yakıt Yoğunluğu</label>
                    <input
                      type="number" step="any"
                      value={form.fuel_density}
                      onChange={(e) => setForm({ ...form, fuel_density: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Karbon Oranı</label>
                    <input
                      type="number" step="any"
                      value={form.fuel_carbon_ratio}
                      onChange={(e) => setForm({ ...form, fuel_carbon_ratio: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">CO₂/Litre</label>
                    <input
                      type="number" step="any"
                      value={form.fuel_co2_per_liter}
                      onChange={(e) => setForm({ ...form, fuel_co2_per_liter: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                </div>
              </details>
            </div>
            <div className="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
              <Button variant="secondary" onClick={() => setShowForm(false)}>İptal</Button>
              <Button onClick={handleSave} disabled={saving || !form.name}>
                {saving ? "Kaydediliyor..." : "Kaydet"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600" />
        </div>
      ) : sources.length === 0 ? (
        <Card>
          <div className="text-center py-12 text-gray-400">
            <Zap className="w-12 h-12 mx-auto mb-3" />
            <p>Henüz enerji kaynağı bulunmuyor</p>
          </div>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-2 font-medium text-gray-500">Adı</th>
                  <th className="text-left py-3 px-2 font-medium text-gray-500">Türkçe</th>
                  <th className="text-left py-3 px-2 font-medium text-gray-500">Kategori</th>
                  <th className="text-center py-3 px-2 font-medium text-gray-500">Birim</th>
                  <th className="text-center py-3 px-2 font-medium text-gray-500">Yenilenebilir</th>
                  <th className="text-center py-3 px-2 font-medium text-gray-500">Durum</th>
                  <th className="text-center py-3 px-2 font-medium text-gray-500">İşlemler</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((s) => (
                  <tr key={s.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-3 px-2 font-medium text-gray-900">{s.name}</td>
                    <td className="py-3 px-2 text-gray-600">{s.name_tr || "-"}</td>
                    <td className="py-3 px-2">
                      <Badge>{s.category}</Badge>
                    </td>
                    <td className="py-3 px-2 text-center text-gray-600">{s.unit}</td>
                    <td className="py-3 px-2 text-center">
                      <Badge variant={s.is_renewable ? "success" : "default"}>
                        {s.is_renewable ? "Evet" : "Hayır"}
                      </Badge>
                    </td>
                    <td className="py-3 px-2 text-center">
                      <Badge variant={s.is_active ? "success" : "warning"}>
                        {s.is_active ? "Aktif" : "Pasif"}
                      </Badge>
                    </td>
                    <td className="py-3 px-2 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <button onClick={() => openEdit(s)} className="p-1.5 hover:bg-gray-100 rounded-lg" title="Düzenle">
                          <Pencil className="w-4 h-4 text-gray-500" />
                        </button>
                        <button onClick={() => handleDelete(s.id, s.name)} className="p-1.5 hover:bg-red-50 rounded-lg" title="Sil">
                          <Trash2 className="w-4 h-4 text-red-400" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
