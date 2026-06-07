"use client"

import { useEffect, useState } from "react"
import { Pencil, X, Users } from "lucide-react"
import { adminApi } from "@/lib/api"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"
import { Badge } from "@/components/ui/Badge"
import { formatDateTime } from "@/lib/utils"
import type { UserDetail } from "@/types"

export default function AdminUsersPage() {
  const [users, setUsers] = useState<UserDetail[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [skip, setSkip] = useState(0)
  const [showEdit, setShowEdit] = useState(false)
  const [editingUser, setEditingUser] = useState<UserDetail | null>(null)
  const [editRole, setEditRole] = useState("viewer")
  const [editActive, setEditActive] = useState(true)
  const [saving, setSaving] = useState(false)
  const limit = 20

  const load = (s = skip) => {
    setLoading(true)
    adminApi.listUsers(s, limit).then((res) => {
      setUsers(res.items)
      setTotal(res.total)
    }).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const openEdit = (u: UserDetail) => {
    setEditingUser(u)
    setEditRole(u.role)
    setEditActive(u.is_active)
    setShowEdit(true)
  }

  const handleSave = async () => {
    if (!editingUser) return
    setSaving(true)
    try {
      await adminApi.updateUser(editingUser.id, { role: editRole, is_active: editActive })
      setShowEdit(false)
      load()
    } finally {
      setSaving(false)
    }
  }

  const totalPages = Math.ceil(total / limit)
  const currentPage = Math.floor(skip / limit) + 1

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Kullanıcı Yönetimi</h1>
        <p className="text-sm text-gray-500 mt-1">Sistemdeki tüm kullanıcıları yönetin</p>
      </div>

      {/* Edit Modal */}
      {showEdit && editingUser && (
        <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900">Kullanıcı Düzenle</h2>
              <button onClick={() => setShowEdit(false)} className="p-1 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div>
                <p className="text-sm text-gray-500">E-posta</p>
                <p className="text-sm font-medium text-gray-900">{editingUser.email}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Ad Soyad</p>
                <p className="text-sm font-medium text-gray-900">{editingUser.full_name}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Rol</label>
                <select
                  value={editRole}
                  onChange={(e) => setEditRole(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="viewer">İzleyici (viewer)</option>
                  <option value="operator">Operatör (operator)</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={editActive}
                  onChange={(e) => setEditActive(e.target.checked)}
                  className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                />
                Aktif
              </label>
            </div>
            <div className="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
              <Button variant="secondary" onClick={() => setShowEdit(false)}>İptal</Button>
              <Button onClick={handleSave} disabled={saving}>
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
      ) : users.length === 0 ? (
        <Card>
          <div className="text-center py-12 text-gray-400">
            <Users className="w-12 h-12 mx-auto mb-3" />
            <p>Henüz kullanıcı bulunmuyor</p>
          </div>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-2 font-medium text-gray-500">Ad Soyad</th>
                  <th className="text-left py-3 px-2 font-medium text-gray-500">E-posta</th>
                  <th className="text-left py-3 px-2 font-medium text-gray-500">Şirket</th>
                  <th className="text-center py-3 px-2 font-medium text-gray-500">Rol</th>
                  <th className="text-center py-3 px-2 font-medium text-gray-500">Durum</th>
                  <th className="text-left py-3 px-2 font-medium text-gray-500">Kayıt</th>
                  <th className="text-center py-3 px-2 font-medium text-gray-500">İşlemler</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-3 px-2 font-medium text-gray-900">{u.full_name}</td>
                    <td className="py-3 px-2 text-gray-600">{u.email}</td>
                    <td className="py-3 px-2 text-gray-500">{u.company_name || "-"}</td>
                    <td className="py-3 px-2 text-center">
                      <Badge variant={u.role === "admin" ? "danger" : u.role === "operator" ? "info" : "default"}>
                        {u.role}
                      </Badge>
                    </td>
                    <td className="py-3 px-2 text-center">
                      <Badge variant={u.is_active ? "success" : "warning"}>
                        {u.is_active ? "Aktif" : "Pasif"}
                      </Badge>
                    </td>
                    <td className="py-3 px-2 text-gray-500 whitespace-nowrap">{formatDateTime(u.created_at)}</td>
                    <td className="py-3 px-2 text-center">
                      <button onClick={() => openEdit(u)} className="p-1.5 hover:bg-gray-100 rounded-lg" title="Düzenle">
                        <Pencil className="w-4 h-4 text-gray-500" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Pagination */}
      {total > limit && (
        <div className="flex items-center justify-between text-sm">
          <p className="text-gray-500">
            Toplam {total} kullanıcıdan {Math.min(skip + 1, total)}-{Math.min(skip + limit, total)} gösteriliyor
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
