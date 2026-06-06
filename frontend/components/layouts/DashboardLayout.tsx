"use client"

import { usePathname, useRouter } from "next/navigation"
import { Sidebar } from "./Sidebar"
import { useAuth } from "@/lib/auth"
import { I18nProvider } from "@/lib/i18n/context"
import { useEffect } from "react"

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const { user, isLoading } = useAuth()
  const isAuthPage =
    pathname.startsWith("/login") || pathname.startsWith("/register")

  useEffect(() => {
    if (!isLoading && !user && !isAuthPage) {
      router.push("/login")
    }
  }, [user, isLoading, isAuthPage, router])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600" />
      </div>
    )
  }

  if (isAuthPage) {
    return <I18nProvider>{children}</I18nProvider>
  }

  if (!user) {
    return null
  }

  return (
    <I18nProvider>
      <div className="min-h-screen bg-gray-50">
        <Sidebar />
        <main className="pl-60 transition-all duration-200">
          <div className="max-w-7xl mx-auto px-6 py-8">{children}</div>
        </main>
      </div>
    </I18nProvider>
  )
}
