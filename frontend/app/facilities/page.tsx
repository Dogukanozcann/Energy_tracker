"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Plus, Building2, MapPin, Users, Eye, Trash2, ExternalLink } from "lucide-react"
import { facilityApi } from "@/lib/api"
import { Card } from "@/components/ui/Card"
import { Button } from "@/components/ui/Button"
import { Badge } from "@/components/ui/Badge"
import { formatDate, formatNumber } from "@/lib/utils"
import type { Facility } from "@/types"

export default function FacilitiesPage() {
  const router = useRouter()
  const [facilities, setFacilities] = useState<Facility[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: "", city: "", district: "", facility_type: "office" })

  const load = () => {
    setLoading(true)
    facilityApi.list().then((res) => {
      setFacilities(res.items)
      setLoading(false)
    })
  }

  useEffect(() => { load() }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    await facilityApi.create(form)
    setShowForm(false)
    setForm({ name: "", city: "", district: "", facility_type: "office" })
    load()
  }

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`"${name}" silinecek. Emin misiniz?`)) return
    await facilityApi.delete(id)
    load()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tesisler</h1>
          <p className="text-sm text-gray-500 mt-1">Tüm tesislerinizi yönetin</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          <Plus className="w-4 h-4" />
          {showForm ? "İptal" : "Tesis Ekle"}
        </Button>
      </div>

      {/* Create Form */}
      {showForm && (
        <Card>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tesis Adı *</label>
                <input
                  required
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  placeholder="Ana Fabrika"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tür</label>
                <select
                  value={form.facility_type}
                  onChange={(e) => setForm({ ...form, facility_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="office">Ofis</option>
                  <option value="factory">Fabrika</option>
                  <option value="warehouse">Depo</option>
                  <option value="retail">Perakende</option>
                  <option value="home">Konut</option>
                  <option value="other">Diğer</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Şehir</label>
                <input
                  value={form.city}
                  onChange={(e) => setForm({ ...form, city: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  placeholder="İstanbul"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">İlçe</label>
                <input
                  value={form.district}
                  onChange={(e) => setForm({ ...form, district: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  placeholder="Tuzla"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setShowForm(false)}>İptal</Button>
              <Button type="submit">Kaydet</Button>
            </div>
          </form>
        </Card>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600" />
        </div>
      )}

      {/* Empty State */}
      {!loading && facilities.length === 0 && (
        <Card>
          <div className="text-center py-12">
            <Building2 className="w-12 h-12 text-gray-300 mx-auto" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">Henüz tesis eklenmemiş</h3>
            <p className="mt-1 text-sm text-gray-500">
              İlk tesisinizi ekleyerek enerji takibine başlayın.
            </p>
          </div>
        </Card>
      )}

      {/* Facility Grid */}
      {!loading && facilities.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {facilities.map((facility) => (
            <div
              key={facility.id}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-50 rounded-lg">
                    <Building2 className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{facility.name}</h3>
                    <p className="text-xs text-gray-500 capitalize">{facility.facility_type}</p>
                  </div>
                </div>
                <Badge variant={facility.is_active ? "success" : "default"}>
                  {facility.is_active ? "Aktif" : "Pasif"}
                </Badge>
              </div>

              <div className="mt-4 space-y-2 text-sm text-gray-500">
                {(facility.city || facility.district) && (
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4" />
                    <span>{[facility.city, facility.district].filter(Boolean).join(", ")}</span>
                  </div>
                )}
                {facility.area_sqm && (
                  <div className="flex items-center gap-2">
                    <Building2 className="w-4 h-4" />
                    <span>{formatNumber(facility.area_sqm, 0)} m²</span>
                  </div>
                )}
                {facility.num_occupants && (
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4" />
                    <span>{facility.num_occupants} kişi</span>
                  </div>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-gray-100 flex gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="flex-1"
                  onClick={() => router.push(`/energy?facility_id=${facility.id}`)}
                >
                  <ExternalLink className="w-4 h-4" /> Enerji
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDelete(facility.id, facility.name)}
                >
                  <Trash2 className="w-4 h-4 text-red-500" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
