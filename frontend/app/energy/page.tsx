"use client"

import { useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import { Zap, Calendar, Filter, Upload } from "lucide-react"
import { facilityApi, consumptionApi } from "@/lib/api"
import { Card } from "@/components/ui/Card"
import { Button } from "@/components/ui/Button"
import { ConsumptionChart } from "@/components/charts/ConsumptionChart"
import { CsvUpload } from "@/components/upload/CsvUpload"
import { formatNumber, formatDateTime } from "@/lib/utils"
import type { Facility, EnergyConsumptionListResponse } from "@/types"

export default function EnergyPage() {
  const searchParams = useSearchParams()
  const [facilities, setFacilities] = useState<Facility[]>([])
  const [selected, setSelected] = useState(searchParams.get("facility_id") || "")
  const [data, setData] = useState<EnergyConsumptionListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [showImport, setShowImport] = useState(false)

  useEffect(() => {
    facilityApi.list().then((res) => {
      setFacilities(res.items)
      if (!selected && res.items.length > 0) {
        setSelected(res.items[0].id)
      }
    })
  }, [])

  useEffect(() => {
    if (!selected) return
    setLoading(true)
    consumptionApi.list(selected, { limit: 50 })
      .then(setData)
      .finally(() => setLoading(false))
  }, [selected])

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
          <Button variant="secondary" size="sm" onClick={() => setShowImport(!showImport)}>
            <Upload className="w-4 h-4" />
            CSV Yükle
          </Button>
        </div>
      </div>

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
