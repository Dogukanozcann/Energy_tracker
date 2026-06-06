"use client"

import { useState, useRef } from "react"
import { Upload, FileText, X, CheckCircle, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"
import { importApi } from "@/lib/api"
import type { BatchImportResponse } from "@/types"

interface CsvUploadProps {
  facilityId: string
  onSuccess?: () => void
}

export function CsvUpload({ facilityId, onSuccess }: CsvUploadProps) {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<BatchImportResponse | null>(null)
  const [error, setError] = useState("")
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f && (f.name.endsWith(".csv") || f.name.endsWith(".txt"))) {
      setFile(f)
      setResult(null)
      setError("")
    } else {
      setError("Lütfen geçerli bir CSV dosyası seçin.")
    }
  }

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    setError("")
    try {
      const res = await importApi.uploadConsumption(facilityId, file)
      setResult(res)
      setFile(null)
      if (onSuccess) onSuccess()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Yükleme hatası")
    } finally {
      setUploading(false)
    }
  }

  const reset = () => {
    setFile(null)
    setResult(null)
    setError("")
    if (inputRef.current) inputRef.current.value = ""
  }

  return (
    <Card>
      <div className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-900">
            <Upload className="w-4 h-4 inline mr-1" />
            CSV ile Veri Yükle
          </h3>
          {result && (
            <button onClick={reset} className="text-gray-400 hover:text-gray-600">
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {result ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <span className="text-green-700 font-medium">{result.message}</span>
            </div>
            {result.errors.length > 0 && (
              <details className="text-xs text-gray-500">
                <summary className="cursor-pointer hover:text-gray-700">
                  {result.errors.length} hata detayı
                </summary>
                <ul className="mt-1 space-y-0.5 max-h-32 overflow-y-auto">
                  {result.errors.map((e, i) => (
                    <li key={i} className="text-red-600">⚠ {e}</li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        ) : (
          <>
            <div
              onClick={() => inputRef.current?.click()}
              className="border-2 border-dashed border-gray-200 rounded-lg p-6 text-center cursor-pointer hover:border-brand-300 hover:bg-brand-50/30 transition-colors"
            >
              <input
                ref={inputRef}
                type="file"
                accept=".csv,.txt"
                onChange={handleFileChange}
                className="hidden"
              />
              {file ? (
                <div className="flex items-center justify-center gap-2">
                  <FileText className="w-5 h-5 text-brand-600" />
                  <span className="text-sm font-medium text-gray-700">{file.name}</span>
                  <span className="text-xs text-gray-400">
                    ({(file.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
              ) : (
                <>
                  <Upload className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">
                    CSV dosyasını seçmek için tıklayın
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    Sütunlar: recorded_at, consumption_value, unit, source, cost
                  </p>
                </>
              )}
            </div>

            {error && (
              <div className="flex items-center gap-2 mt-2 text-sm text-red-600">
                <AlertCircle className="w-4 h-4" /> {error}
              </div>
            )}

            {file && (
              <div className="flex justify-end mt-3">
                <Button size="sm" onClick={handleUpload} disabled={uploading}>
                  {uploading ? "Yükleniyor..." : "Yüklemeyi Başlat"}
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </Card>
  )
}
