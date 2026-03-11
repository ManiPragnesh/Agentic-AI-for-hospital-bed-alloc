import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowUpIcon, ArrowDownIcon, Activity } from "lucide-react"

interface StatCardProps {
  title: string
  value: string | number
  subtext?: string
  trend?: "up" | "down" | "neutral"
  icon?: React.ReactNode
  color?: string
}

export function StatCard({ title, value, subtext, trend, icon, color = "text-blue-500" }: StatCardProps) {
  return (
    <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100 dark:bg-slate-900 dark:border-slate-800">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{title}</p>
          <h3 className="text-2xl font-bold mt-1 text-slate-900 dark:text-white">{value}</h3>
        </div>
        <div className={`p-2 bg-slate-50 dark:bg-slate-800 rounded-lg ${color}`}>
          {icon || <Activity className="w-5 h-5" />}
        </div>
      </div>
      {subtext && (
        <div className="mt-2 flex items-center text-xs text-slate-500">
            {trend === "up" && <ArrowUpIcon className="w-3 h-3 text-red-500 mr-1" />}
            {trend === "down" && <ArrowDownIcon className="w-3 h-3 text-green-500 mr-1" />}
            {subtext}
        </div>
      )}
    </div>
  )
}
