"use client"

import { useEffect, useState } from "react"
import { Bell, AlertTriangle, CheckCircle, XCircle, Eye, RefreshCw } from "lucide-react"
import { facilityApi, alertApi } from "@/lib/api"
import { Card } from "@/components/ui/Card"
import { Button } from "@/components/ui/Button"
import { Badge } from "@/components/ui/Badge"
import { formatDateTime, getSeverityColor, getStatusColor } from "@/lib/utils"
import type { Facility, AlertListResponse } from "@/types"

const SEVERITY_ORDER = ["critical", "high", "medium", "low"]

export default function AlertsPage() {
  const [facilities, setFacilities] = useState<Facility[]>([])
  const [selected, setSelected] = useState("")
  const [data, setData] = useState<AlertListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState("")

  useEffect(() => {
    facilityApi.list().then((res) => {
      setFacilities(res.items)
      if (res.items.length > 0) setSelected(res.items[0].id)
    })
  }, [])

  useEffect(() => {
    if (!selected) return
    setLoading(true)
    alertApi
      .list(selected, { status: statusFilter || undefined, limit: 100 })
      .then(setData)
      .finally(() => setLoading(false))
  }, [selected, statusFilter])

  const handleStatusChange = async (id: string, newStatus: string) => {
    await alertApi.updateStatus(id, newStatus)
    // Refresh
    const updated = await alertApi.list(selected, { status: statusFilter || undefined, limit: 100 })
    setData(updated)
  }

  const handleDetect = async () => {
    if (!selected) return
    await alertApi.detect(selected)
    const updated = await alertApi.list(selected, { status: statusFilter || undefined, limit: 100 })
    setData(updated)
  }

  const alerts = data?.items ?? []
  // Severity'e göre sırala
  alerts.sort(
    (a, b) => SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity),
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Uyarılar</h1>
          <p className="text-sm text-gray-500 mt-1">
            {data ? `${data.new_count} yeni, ${data.critical_count} kritik` : ""}
          </p>
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
          <Button variant="secondary" size="sm" onClick={handleDetect}>
            <RefreshCw className="w-4 h-4" />
            Anomali Tara
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {["", "new", "acknowledged", "resolved"].map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              statusFilter === s
                ? "bg-brand-50 text-brand-700 border border-brand-200"
                : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
            }`}
          >
            {s === "" ? "Tümü" : s === "new" ? "Yeni" : s === "acknowledged" ? "İnceleniyor" : "Çözülmüş"}
          </button>
        ))}
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600" />
        </div>
      )}

      {/* Alert List */}
      {!loading && alerts.length === 0 && (
        <Card>
          <div className="text-center py-12 text-gray-400">
            <Bell className="w-12 h-12 mx-auto mb-3" />
            <p>Henüz uyarı bulunmuyor</p>
          </div>
        </Card>
      )}

      {!loading && alerts.length > 0 && (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-start gap-4">
                {/* Severity Icon */}
                <div className={`p-2 rounded-lg ${
                  alert.severity === "critical" ? "bg-red-50" :
                  alert.severity === "high" ? "bg-orange-50" :
                  alert.severity === "medium" ? "bg-yellow-50" : "bg-blue-50"
                }`}>
                  <AlertTriangle className={`w-5 h-5 ${
                    alert.severity === "critical" ? "text-red-500" :
                    alert.severity === "high" ? "text-orange-500" :
                    alert.severity === "medium" ? "text-yellow-500" : "text-blue-500"
                  }`} />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-sm font-semibold text-gray-900">{alert.title}</h3>
                    <Badge variant={
                      alert.severity === "critical" ? "danger" :
                      alert.severity === "high" ? "warning" :
                      alert.severity === "medium" ? "info" : "default"
                    }>
                      {alert.severity}
                    </Badge>
                    <Badge variant={
                      alert.status === "new" ? "danger" :
                      alert.status === "acknowledged" ? "warning" :
                      alert.status === "resolved" ? "success" : "default"
                    }>
                      {alert.status === "new" ? "Yeni" :
                       alert.status === "acknowledged" ? "İnceleniyor" :
                       alert.status === "resolved" ? "Çözüldü" : "Kapatıldı"}
                    </Badge>
                  </div>

                  {alert.description && (
                    <p className="text-sm text-gray-600 mt-1">{alert.description}</p>
                  )}

                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                    <span>{formatDateTime(alert.detected_at)}</span>
                    {alert.deviation_percent != null && (
                      <span>Sapma: %{Math.abs(alert.deviation_percent).toFixed(1)}</span>
                    )}
                    {alert.category && (
                      <span className="capitalize">{alert.category.replace("_", " ")}</span>
                    )}
                  </div>

                  {alert.recommendation_text && (
                    <div className="mt-2 p-3 bg-gray-50 rounded-lg text-sm text-gray-600">
                      💡 {alert.recommendation_text}
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex flex-col gap-1.5 shrink-0">
                  {alert.status === "new" && (
                    <Button variant="ghost" size="sm" onClick={() => handleStatusChange(alert.id, "acknowledged")}>
                      <Eye className="w-4 h-4" /> İncele
                    </Button>
                  )}
                  {alert.status === "acknowledged" && (
                    <>
                      <Button variant="ghost" size="sm" onClick={() => handleStatusChange(alert.id, "resolved")}>
                        <CheckCircle className="w-4 h-4 text-green-600" /> Çöz
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => handleStatusChange(alert.id, "dismissed")}>
                        <XCircle className="w-4 h-4 text-gray-400" /> Kapat
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
