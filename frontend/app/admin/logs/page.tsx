"use client"

import { useEffect, useState } from "react"
import { ClipboardList } from "lucide-react"
import { adminApi } from "@/lib/api"
import { Card } from "@/components/ui/Card"
import { Badge } from "@/components/ui/Badge"
import { Button } from "@/components/ui/Button"
import { formatDateTime } from "@/lib/utils"
import type { AuditLogEntry } from "@/types"

const actionColors: Record<string, "success" | "info" | "danger" | "default"> = {
  create: "success",
  update: "info",
  delete: "danger",
}

export default function AdminLogsPage() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [skip, setSkip] = useState(0)
  const limit = 20

  const load = (s = skip) => {
    setLoading(true)
    adminApi.listLogs(s, limit).then((res) => {
      setLogs(res.items)
      setTotal(res.total)
    }).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const totalPages = Math.ceil(total / limit)
  const currentPage = Math.floor(skip / limit) + 1

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Denetim Kayıtları</h1>
        <p className="text-sm text-gray-500 mt-1">Tüm admin işlem geçmişi</p>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600" />
        </div>
      ) : logs.length === 0 ? (
        <Card>
          <div className="text-center py-12 text-gray-400">
            <ClipboardList className="w-12 h-12 mx-auto mb-3" />
            <p>Henüz denetim kaydı bulunmuyor</p>
          </div>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-2 font-medium text-gray-500">Tarih</th>
                  <th className="text-left py-3 px-2 font-medium text-gray-500">Kullanıcı</th>
                  <th className="text-center py-3 px-2 font-medium text-gray-500">İşlem</th>
                  <th className="text-left py-3 px-2 font-medium text-gray-500">Kaynak</th>
                  <th className="text-left py-3 px-2 font-medium text-gray-500">Kaynak ID</th>
                  <th className="text-left py-3 px-2 font-medium text-gray-500">Detay</th>
                  <th className="text-left py-3 px-2 font-medium text-gray-500">IP</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => {
                  const rowBg = log.action === "delete" ? "bg-red-50/30" : log.action === "create" ? "bg-green-50/30" : ""
                  return (
                    <tr key={log.id} className={`border-b border-gray-50 hover:bg-gray-50 ${rowBg}`}>
                      <td className="py-3 px-2 text-gray-600 whitespace-nowrap">{formatDateTime(log.created_at)}</td>
                      <td className="py-3 px-2 text-gray-700">{log.user_email || "-"}</td>
                      <td className="py-3 px-2 text-center">
                        <Badge variant={actionColors[log.action] || "default"}>{log.action}</Badge>
                      </td>
                      <td className="py-3 px-2 text-gray-600">{log.resource}</td>
                      <td className="py-3 px-2 text-gray-500 font-mono text-xs">
                        {log.resource_id ? log.resource_id.slice(0, 8) + "..." : "-"}
                      </td>
                      <td className="py-3 px-2 text-gray-500 max-w-xs truncate">{log.details || "-"}</td>
                      <td className="py-3 px-2 text-gray-400 font-mono text-xs">{log.ip_address || "-"}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Pagination */}
      {total > limit && (
        <div className="flex items-center justify-between text-sm">
          <p className="text-gray-500">
            Toplam {total} kayıttan {Math.min(skip + 1, total)}-{Math.min(skip + limit, total)} gösteriliyor
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="secondary" size="sm"
              disabled={skip === 0}
              onClick={() => { setSkip(skip - limit); load(skip - limit) }}
            >
              Önceki
            </Button>
            <span className="text-gray-500 px-2">Sayfa {currentPage} / {totalPages}</span>
            <Button
              variant="secondary" size="sm"
              disabled={skip + limit >= total}
              onClick={() => { setSkip(skip + limit); load(skip + limit) }}
            >
              Sonraki
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
