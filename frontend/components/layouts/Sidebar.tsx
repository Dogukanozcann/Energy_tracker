"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard,
  Building2,
  Zap,
  Leaf,
  Bell,
  LogOut,
  ChevronLeft,
  Globe,
  Settings,
  Shield,
  Users,
  ClipboardList,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuth } from "@/lib/auth"
import { useTranslation } from "@/lib/i18n/context"
import { useState } from "react"

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/facilities", label: "Tesisler", icon: Building2 },
  { href: "/energy", label: "Enerji", icon: Zap },
  { href: "/alerts", label: "Uyarılar", icon: Bell },
]

const adminNavItems = [
  { href: "/admin", label: "Admin Panel", icon: Shield },
  { href: "/admin/energy-sources", label: "Enerji Kaynakları", icon: Zap },
  { href: "/admin/users", label: "Kullanıcılar", icon: Users },
  { href: "/admin/settings", label: "Sistem Ayarları", icon: Settings },
  { href: "/admin/logs", label: "Denetim Kayıtları", icon: ClipboardList },
]

export function Sidebar() {
  const pathname = usePathname()
  const { logout, user } = useAuth()
  const { t, toggleLocale, locale } = useTranslation()
  const [collapsed, setCollapsed] = useState(false)

  // Login/register/forgot/reset sayfalarında gizle
  if (
    pathname.startsWith("/login") ||
    pathname.startsWith("/register") ||
    pathname.startsWith("/forgot-password") ||
    pathname.startsWith("/reset-password")
  ) {
    return null
  }

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 h-full bg-white border-r border-gray-200 z-40 flex flex-col transition-all duration-200",
        collapsed ? "w-16" : "w-60",
      )}
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b border-gray-100">
        <Leaf className="w-7 h-7 text-brand-600 shrink-0" />
        {!collapsed && (
          <span className="ml-3 font-bold text-gray-900 whitespace-nowrap">
            EnergyTracker
          </span>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="ml-auto p-1 rounded-lg hover:bg-gray-100 text-gray-400"
        >
          <ChevronLeft
            className={cn("w-4 h-4 transition-transform", collapsed && "rotate-180")}
          />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const active = pathname.startsWith(item.href)
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                active
                  ? "bg-brand-50 text-brand-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900",
              )}
            >
              <item.icon className="w-5 h-5 shrink-0" />
              {!collapsed && <span className="ml-3">{item.label}</span>}
            </Link>
          )
        })}

        {user?.role === "admin" && !collapsed && (
          <div className="pt-3 pb-1">
            <p className="px-3 text-xs font-semibold uppercase tracking-wider text-gray-400">
              Yönetim
            </p>
          </div>
        )}

        {user?.role === "admin" &&
          adminNavItems.map((item) => {
            const active = pathname.startsWith(item.href)
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                  active
                    ? "bg-brand-50 text-brand-700"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900",
                )}
              >
                <item.icon className="w-5 h-5 shrink-0" />
                {!collapsed && <span className="ml-3">{item.label}</span>}
              </Link>
            )
          })}
      </nav>

      {/* User */}
      {!collapsed && user && (
        <div className="px-4 py-3 border-t border-gray-100">
          <p className="text-sm font-medium text-gray-900 truncate">
            {user.full_name}
          </p>
          <p className="text-xs text-gray-500 truncate">{user.email}</p>
        </div>
      )}

      {/* Language Switcher */}
      <div className="px-2">
        <button
          onClick={toggleLocale}
          className="flex items-center w-full px-3 py-2.5 text-sm font-medium text-gray-600 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <Globe className="w-5 h-5 shrink-0" />
          {!collapsed && (
            <span className="ml-3">{locale === "tr" ? "English" : "Türkçe"}</span>
          )}
        </button>
      </div>

      {/* Logout */}
      <div className="p-2">
        <button
          onClick={logout}
          className="flex items-center w-full px-3 py-2.5 text-sm font-medium text-gray-600 rounded-lg hover:bg-gray-50 hover:text-red-600 transition-colors"
        >
          <LogOut className="w-5 h-5 shrink-0" />
          {!collapsed && <span className="ml-3">{t("nav.logout")}</span>}
        </button>
      </div>
    </aside>
  )
}
