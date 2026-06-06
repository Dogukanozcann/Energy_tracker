export type Locale = "tr" | "en"

export type TranslationKey =
  | "nav.dashboard"
  | "nav.facilities"
  | "nav.energy"
  | "nav.alerts"
  | "nav.logout"
  | "nav.reports"
  | "auth.login"
  | "auth.register"
  | "auth.email"
  | "auth.password"
  | "auth.fullName"
  | "auth.forgotPassword"
  | "auth.resetPassword"
  | "auth.sendLink"
  | "auth.newPassword"
  | "auth.verifyEmail"
  | "common.loading"
  | "common.save"
  | "common.cancel"
  | "common.delete"
  | "common.search"
  | "common.download"
  | "common.upload"
  | "common.export"
  | "common.import"
  | "dashboard.title"
  | "dashboard.totalConsumption"
  | "dashboard.totalCost"
  | "dashboard.carbonFootprint"
  | "dashboard.activeAlerts"
  | "dashboard.facilityCount"
  | "dashboard.calculateCarbon"
  | "dashboard.recentAlerts"
  | "facility.title"
  | "facility.add"
  | "facility.name"
  | "facility.type"
  | "energy.title"
  | "energy.importCsv"
  | "alerts.title"
  | "alerts.scanAnomalies"
  | "alerts.noAlerts"
  | "report.carbonTitle"
  | "lang.switch"

const translations: Record<Locale, Record<TranslationKey, string>> = {
  tr: {
    "nav.dashboard": "Dashboard",
    "nav.facilities": "Tesisler",
    "nav.energy": "Enerji",
    "nav.alerts": "Uyarılar",
    "nav.logout": "Çıkış",
    "nav.reports": "Raporlar",
    "auth.login": "Giriş Yap",
    "auth.register": "Kayıt Ol",
    "auth.email": "E-posta",
    "auth.password": "Şifre",
    "auth.fullName": "Ad Soyad",
    "auth.forgotPassword": "Şifremi Unuttum",
    "auth.resetPassword": "Şifre Sıfırla",
    "auth.sendLink": "Bağlantı Gönder",
    "auth.newPassword": "Yeni Şifre",
    "auth.verifyEmail": "E-posta Doğrula",
    "common.loading": "Yükleniyor...",
    "common.save": "Kaydet",
    "common.cancel": "İptal",
    "common.delete": "Sil",
    "common.search": "Ara",
    "common.download": "İndir",
    "common.upload": "Yükle",
    "common.export": "Dışa Aktar",
    "common.import": "İçe Aktar",
    "dashboard.title": "Dashboard",
    "dashboard.totalConsumption": "Toplam Tüketim",
    "dashboard.totalCost": "Toplam Maliyet",
    "dashboard.carbonFootprint": "Karbon Ayak İzi",
    "dashboard.activeAlerts": "Aktif Uyarılar",
    "dashboard.facilityCount": "Tesis Sayısı",
    "dashboard.calculateCarbon": "Karbon Hesapla",
    "dashboard.recentAlerts": "Son Uyarılar",
    "facility.title": "Tesisler",
    "facility.add": "Tesis Ekle",
    "facility.name": "Tesis Adı",
    "facility.type": "Tesis Türü",
    "energy.title": "Enerji Tüketimi",
    "energy.importCsv": "CSV ile Veri Yükle",
    "alerts.title": "Uyarılar",
    "alerts.scanAnomalies": "Anomali Tara",
    "alerts.noAlerts": "Henüz uyarı bulunmuyor",
    "report.carbonTitle": "Karbon Raporu İndir",
    "lang.switch": "English",
  },
  en: {
    "nav.dashboard": "Dashboard",
    "nav.facilities": "Facilities",
    "nav.energy": "Energy",
    "nav.alerts": "Alerts",
    "nav.logout": "Logout",
    "nav.reports": "Reports",
    "auth.login": "Login",
    "auth.register": "Register",
    "auth.email": "Email",
    "auth.password": "Password",
    "auth.fullName": "Full Name",
    "auth.forgotPassword": "Forgot Password",
    "auth.resetPassword": "Reset Password",
    "auth.sendLink": "Send Link",
    "auth.newPassword": "New Password",
    "auth.verifyEmail": "Verify Email",
    "common.loading": "Loading...",
    "common.save": "Save",
    "common.cancel": "Cancel",
    "common.delete": "Delete",
    "common.search": "Search",
    "common.download": "Download",
    "common.upload": "Upload",
    "common.export": "Export",
    "common.import": "Import",
    "dashboard.title": "Dashboard",
    "dashboard.totalConsumption": "Total Consumption",
    "dashboard.totalCost": "Total Cost",
    "dashboard.carbonFootprint": "Carbon Footprint",
    "dashboard.activeAlerts": "Active Alerts",
    "dashboard.facilityCount": "Facilities",
    "dashboard.calculateCarbon": "Calculate Carbon",
    "dashboard.recentAlerts": "Recent Alerts",
    "facility.title": "Facilities",
    "facility.add": "Add Facility",
    "facility.name": "Facility Name",
    "facility.type": "Facility Type",
    "energy.title": "Energy Consumption",
    "energy.importCsv": "Import CSV Data",
    "alerts.title": "Alerts",
    "alerts.scanAnomalies": "Scan Anomalies",
    "alerts.noAlerts": "No alerts yet",
    "report.carbonTitle": "Download Carbon Report",
    "lang.switch": "Türkçe",
  },
}

export default translations
