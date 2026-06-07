"use client"

import { useEffect, useState } from "react"
import { Shield, Zap, Users, Settings, ClipboardList } from "lucide-react"
import { adminApi } from "@/lib/api"
import { Card } from "@/components/ui/Card"
import { Badge } from "@/components/ui/Badge"
import { formatDateTime } from "@/lib/utils"
import type { AuditLogEntry } from "@/types"

export default function AdminDashboardPage() {
  const [stats, setStats] = useState({ users: 0, sources: 0, settings: 0, logs: 0 })
  const [recentLogs, setRecentLogs] = useState<AuditLogEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      adminApi.listUsers(0, 1),
      adminApi.listSources(),
      adminApi.listSettings(),
      adminApi.listLogs(0, 10),
    ]).then(([usersRes, sources, settingsRes, logsRes]) => {
      setStats({
        users: usersRes.total,
        sources: sources.length,
        settings: settingsRes.total,
        logs: logsRes.total,
      })
      setRecentLogs(logsRes.items)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600" />
      </div>
    )
  }

  const statCards = [
    { label: "Kullanıcılar", value: stats.users, icon: Users, color: "text-blue-600 bg-blue-50" },
    { label: "Enerji Kaynakları", value: stats.sources, icon: Zap, color: "text-green-600 bg-green-50" },
    { label: "Sistem Ayarları", value: stats.settings, icon: Settings, color: "text-purple-600 bg-purple-50" },
    { label: "Denetim Kayıtları", value: stats.logs, icon: ClipboardList, color: "text-orange-600 bg-orange-50" },
  ]

  const actionBadge = (action: string) => {
    const colors: Record<string, string> = {
      create: "success",
      update: "info",
      delete: "danger",
    }
    return <Badge variant={colors[action] || "default"}>{action}</Badge>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Admin Paneli</h1>
        <p className="text-sm text-gray-500 mt-1">Sistem yönetimi ve denetim</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card) => (
          <Card key={card.label}>
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-lg ${card.color}`}>
                <card.icon className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm text-gray-500">{card.label}</p>
                <p className="text-2xl font-bold text-gray-900">{card.value}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Recent Logs */}
      <Card title="Son İşlemler">
        {recentLogs.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <ClipboardList className="w-10 h-10 mx-auto mb-2" />
            <p className="text-sm">Henüz işlem kaydı bulunmuyor</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-2 font-medium text-gray-500">Tarih</th>
                  <th className="text-left py-2 px-2 font-medium text-gray-500">Kullanıcı</th>
                  <th className="text-center py-2 px-2 font-medium text-gray-500">İşlem</th>
                  <th className="text-left py-2 px-2 font-medium text-gray-500">Kaynak</th>
                  <th className="text-left py-2 px-2 font-medium text-gray-500">Detay</th>
                </tr>
              </thead>
              <tbody>
                {recentLogs.map((log) => (
                  <tr key={log.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2 px-2 text-gray-600 whitespace-nowrap">{formatDateTime(log.created_at)}</td>
                    <td className="py-2 px-2 text-gray-700">{log.user_email || "-"}</td>
                    <td className="py-2 px-2 text-center">{actionBadge(log.action)}</td>
                    <td className="py-2 px-2 text-gray-600">{log.resource}</td>
                    <td className="py-2 px-2 text-gray-500 max-w-xs truncate">{log.details || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
