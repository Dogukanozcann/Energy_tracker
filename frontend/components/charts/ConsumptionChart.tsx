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

export type ChartMode = "consumption" | "cost" | "net" | "combined"

interface DataPoint {
  label: string
  value?: number
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

const COMMON_MARGIN = { top: 10, right: 10, left: 30, bottom: 5 }

function sharedTooltipStyle() {
  return {
    borderRadius: "8px",
    border: "1px solid #e5e7eb",
    boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
  } as const
}

function formatVal(v: number) {
  return v.toLocaleString("tr-TR")
}

export function ConsumptionChart({ data, title, mode = "consumption" }: ConsumptionChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400 text-sm">
        Henüz veri bulunmuyor
      </div>
    )
  }

  if (mode === "combined") {
    return (
      <ChartContainer title={title}>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={data} margin={COMMON_MARGIN}>
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
              contentStyle={sharedTooltipStyle()}
              formatter={(value: number, name: string) => {
                switch (name) {
                  case "consumption":
                    return [`${formatVal(value)} kWh/m³`, "Tüketim"]
                  case "production":
                    return [`${formatVal(value)} kWh`, "Üretim"]
                  case "cost":
                    return [`${formatVal(value)} ₺`, "Maliyet"]
                  default:
                    return [formatVal(value), name]
                }
              }}
            />
            <Legend />
            <Bar
              dataKey="consumption"
              fill="#ef4444"
              radius={[4, 4, 0, 0]}
              name="Tüketim"
              maxBarSize={24}
            />
            <Bar
              dataKey="production"
              fill="#22a840"
              radius={[4, 4, 0, 0]}
              name="Üretim"
              maxBarSize={24}
            />
            <Bar
              dataKey="cost"
              fill="#2563eb"
              radius={[4, 4, 0, 0]}
              name="Maliyet"
              maxBarSize={24}
            />
          </BarChart>
        </ResponsiveContainer>
      </ChartContainer>
    )
  }

  if (mode === "net") {
    return (
      <ChartContainer title={title}>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={data} margin={COMMON_MARGIN}>
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
              contentStyle={sharedTooltipStyle()}
              formatter={(value: number, name: string) => [
                `${formatVal(value)} ₺`,
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

  // Legacy modes (consumption / cost) — single bar
  const MODE_CONFIG = {
    consumption: { barKey: "value", barColor: "#22a840", unit: "kWh", tooltipLabel: "Tüketim" },
    cost: { barKey: "cost", barColor: "#2563eb", unit: "₺", tooltipLabel: "Maliyet" },
  } as const
  const config = MODE_CONFIG[mode as keyof typeof MODE_CONFIG]

  return (
    <ChartContainer title={title}>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} margin={COMMON_MARGIN}>
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
            contentStyle={sharedTooltipStyle()}
            formatter={(value: number) => [
              `${formatVal(value)} ${config.unit}`,
              config.tooltipLabel,
            ]}
          />
          <Legend />
          <Bar
            dataKey={config.barKey}
            fill={config.barColor}
            radius={[4, 4, 0, 0]}
            name={config.unit}
            maxBarSize={48}
          />
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}

function ChartContainer({ title, children }: { title?: string; children: React.ReactNode }) {
  return (
    <div className="overflow-hidden">
      {title && (
        <h4 className="text-sm font-medium text-gray-700 mb-3">{title}</h4>
      )}
      {children}
    </div>
  )
}
