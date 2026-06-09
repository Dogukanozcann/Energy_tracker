"use client"

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts"

export type ChartMode = "consumption" | "cost" | "net"

interface DataPoint {
  label: string
  value: number
  cost?: number
  type?: "consumption" | "production"
  consumption?: number
  production?: number
}

interface ConsumptionChartProps {
  data: DataPoint[]
  title?: string
  unit?: string
  mode?: ChartMode
}

const MODE_CONFIG: Record<ChartMode, {
  barKey: string
  barColor: string
  unit: string
  tooltipLabel: string
}> = {
  consumption: {
    barKey: "value",
    barColor: "#22a840",
    unit: "kWh",
    tooltipLabel: "Tüketim",
  },
  cost: {
    barKey: "cost",
    barColor: "#2563eb",
    unit: "₺",
    tooltipLabel: "Maliyet",
  },
  net: {
    barKey: "value",
    barColor: "#f59e0b",
    unit: "₺",
    tooltipLabel: "Net",
  },
}

export function ConsumptionChart({ data, title, unit: propUnit, mode = "consumption" }: ConsumptionChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400 text-sm">
        Henüz veri bulunmuyor
      </div>
    )
  }

  const config = MODE_CONFIG[mode]
  const unit = propUnit || config.unit

  if (mode === "net") {
    return (
      <ChartContainer title={title}>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 12, fill: "#6b7280" }}
              axisLine={{ stroke: "#e5e7eb" }}
            />
            <YAxis
              tick={{ fontSize: 12, fill: "#6b7280" }}
              axisLine={{ stroke: "#e5e7eb" }}
              tickFormatter={(v) => `${v}`}
            />
            <Tooltip
              contentStyle={{
                borderRadius: "8px",
                border: "1px solid #e5e7eb",
                boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
              }}
              formatter={(value: number, name: string) => [
                `${value.toLocaleString("tr-TR")} ₺`,
                name === "consumption" ? "Tüketim Maliyeti" : "Üretim Geliri",
              ]}
            />
            <Legend />
            <Bar
              dataKey="consumption"
              fill="#ef4444"
              radius={[4, 4, 0, 0]}
              name="Tüketim Maliyeti"
              maxBarSize={32}
            />
            <Bar
              dataKey="production"
              fill="#22a840"
              radius={[4, 4, 0, 0]}
              name="Üretim Geliri"
              maxBarSize={32}
            />
          </BarChart>
        </ResponsiveContainer>
      </ChartContainer>
    )
  }

  return (
    <ChartContainer title={title}>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 12, fill: "#6b7280" }}
            axisLine={{ stroke: "#e5e7eb" }}
          />
          <YAxis
            tick={{ fontSize: 12, fill: "#6b7280" }}
            axisLine={{ stroke: "#e5e7eb" }}
            tickFormatter={(v) => `${v}`}
          />
          <Tooltip
            contentStyle={{
              borderRadius: "8px",
              border: "1px solid #e5e7eb",
              boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
            }}
            formatter={(value: number) => [
              `${value.toLocaleString("tr-TR")} ${unit}`,
              config.tooltipLabel,
            ]}
          />
          <Legend />
          <Bar
            dataKey={config.barKey}
            fill={config.barColor}
            radius={[4, 4, 0, 0]}
            name={unit}
            maxBarSize={48}
          />
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}

function ChartContainer({ title, children }: { title?: string; children: React.ReactNode }) {
  return (
    <div>
      {title && (
        <h4 className="text-sm font-medium text-gray-700 mb-3">{title}</h4>
      )}
      {children}
    </div>
  )
}
