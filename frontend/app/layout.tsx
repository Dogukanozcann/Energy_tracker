import type { Metadata } from "next"
import "./globals.css"
import { AuthProvider } from "@/lib/auth"
import { DashboardLayout } from "@/components/layouts/DashboardLayout"

export const metadata: Metadata = {
  title: "EnergyTracker — Enerji Verimliliği Platformu",
  description:
    "Karbon ayak izi takibi, enerji tüketim analizi ve AI destekli tasarruf önerileri.",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="tr">
      <body className="antialiased">
        <AuthProvider>
          <DashboardLayout>{children}</DashboardLayout>
        </AuthProvider>
      </body>
    </html>
  )
}
