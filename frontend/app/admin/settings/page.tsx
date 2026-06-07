"use client"

import { useEffect, useState } from "react"
import { Plus, Pencil, Trash2, X, Settings } from "lucide-react"
import { adminApi } from "@/lib/api"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"
import { Badge } from "@/components/ui/Badge"
import type { SystemSetting } from "@/types"

interface FormData {
  key: string
  value: string
  description: string
  category: string
}

const defaultForm: FormData = { key: "", value: "", description: "", category: "general" }

const categories = ["general", "carbon", "alert", "system"]

export default function AdminSettingsPage() {
  const [items, setItems] = useState<SystemSetting[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [filterCategory, setFilterCategory] = useState("")
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<FormData>(defaultForm)
  const [saving, setSaving] = useState(false)

  const load = (cat?: string) => {
    setLoading(true)
    adminApi.listSettings(cat || undefined)
      .then((res) => { setItems(res.items); setTotal(res.total) })
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  useEffect(() => { load(filterCategory) }, [filterCategory])

  const openCreate = () => {
    setForm(defaultForm)
    setEditingId(null)
    setShowForm(true)
  }

  const openEdit = (s: SystemSetting) => {
    setForm({ key: s.key, value: s.value, description: s.description || "", category: s.category })
    setEditingId(s.id)
    setShowForm(true)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      if (editingId) {
        await adminApi.updateSetting(editingId, form)
      } else {
        await adminApi.createSetting(form)
      }
      setShowForm(false)
      load(filterCategory)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string, key: string) => {
    if (!window.confirm(`"${key}" ayarını silmek istediğinize emin misiniz?`)) return
    await adminApi.deleteSetting(id)
    load(filterCategory)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Sistem Ayarları</h1>
          <p className="text-sm text-gray-500 mt-1">Sistem yapılandırma ayarlarını yönetin</p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="w-4 h-4" />
          Yeni Ayar Ekle
        </Button>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-500">Kategori:</span>
        {["", ...categories].map((cat) => (
          <button
            key={cat}
            onClick={() => setFilterCategory(cat)}
            className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
              filterCategory === cat
                ? "bg-brand-50 text-brand-700 font-medium"
                : "text-gray-600 hover:bg-gray-50"
            }`}
          >
            {cat || "Tümü"}
          </button>
        ))}
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900">
                {editingId ? "Ayarı Düzenle" : "Yeni Ayar Ekle"}
              </h2>
              <button onClick={() => setShowForm(false)} className="p-1 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Anahtar *</label>
                <input
                  value={form.key}
                  onChange={(e) => setForm({ ...form, key: e.target.value })}
                  disabled={!!editingId}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:bg-gray-50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Değer *</label>
                <input
                  value={form.value}
                  onChange={(e) => setForm({ ...form, value: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Açıklama</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  rows={2}
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
                  {categories.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
              <Button variant="secondary" onClick={() => setShowForm(false)}>İptal</Button>
              <Button onClick={handleSave} disabled={saving || !form.key || !form.value}>
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
      ) : items.length === 0 ? (
        <Card>
          <div className="text-center py-12 text-gray-400">
            <Settings className="w-12 h-12 mx-auto mb-3" />
            <p>Henüz ayar bulunmuyor</p>
          </div>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-2 font-medium text-gray-500">Anahtar</th>
                  <th className="text-left py-3 px-2 font-medium text-gray-500">Değer</th>
                  <th className="text-left py-3 px-2 font-medium text-gray-500">Açıklama</th>
                  <th className="text-center py-3 px-2 font-medium text-gray-500">Kategori</th>
                  <th className="text-center py-3 px-2 font-medium text-gray-500">İşlemler</th>
                </tr>
              </thead>
              <tbody>
                {items.map((s) => (
                  <tr key={s.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-3 px-2 font-mono text-sm font-medium text-gray-900">{s.key}</td>
                    <td className="py-3 px-2 text-gray-600 max-w-[200px] truncate">{s.value}</td>
                    <td className="py-3 px-2 text-gray-500 max-w-[200px] truncate">{s.description || "-"}</td>
                    <td className="py-3 px-2 text-center">
                      <Badge>{s.category}</Badge>
                    </td>
                    <td className="py-3 px-2 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <button onClick={() => openEdit(s)} className="p-1.5 hover:bg-gray-100 rounded-lg" title="Düzenle">
                          <Pencil className="w-4 h-4 text-gray-500" />
                        </button>
                        <button onClick={() => handleDelete(s.id, s.key)} className="p-1.5 hover:bg-red-50 rounded-lg" title="Sil">
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
