import {
  BarChart,
  Bar,
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { PlotData } from "../types";

const GOLD = "#C5A059";

interface Props {
  plot: PlotData;
}

export default function DataPlot({ plot }: Props) {
  // Build data array from x/y values
  const data = plot.x_values.map((x, i) => ({
    x: x,
    y: plot.y_values[i],
  }));

  const tooltipStyle = {
    backgroundColor: "white",
    border: "1px solid #e7e5e4",
    borderRadius: "8px",
    fontSize: "12px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
  };

  const axisProps = {
    tick: { fontSize: 10, fill: "#a8a29e" },
    tickLine: false as const,
    axisLine: { stroke: "#d6d3d1" },
  };

  return (
    <div>
      <div className="text-xs font-medium text-stone-600 mb-2">{plot.title}</div>
      <div className="bg-nobel-cream rounded-lg p-3 border border-stone-100">
        <ResponsiveContainer width="100%" height={240}>
          {plot.plot_type === "bar" || plot.plot_type === "histogram" ? (
            <BarChart data={data} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
              <XAxis dataKey="x" {...axisProps} />
              <YAxis {...axisProps} width={50} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="y" fill={GOLD} radius={[4, 4, 0, 0]} name={plot.y_label} />
            </BarChart>
          ) : plot.plot_type === "scatter" ? (
            <ScatterChart margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
              <XAxis dataKey="x" {...axisProps} name={plot.x_label} />
              <YAxis dataKey="y" {...axisProps} width={50} name={plot.y_label} />
              <Tooltip contentStyle={tooltipStyle} />
              <Scatter data={data} fill={GOLD} />
            </ScatterChart>
          ) : (
            <LineChart data={data} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
              <XAxis dataKey="x" {...axisProps} />
              <YAxis {...axisProps} width={50} />
              <Tooltip contentStyle={tooltipStyle} />
              <Line
                type="monotone"
                dataKey="y"
                stroke={GOLD}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 3, strokeWidth: 0 }}
                name={plot.y_label}
              />
            </LineChart>
          )}
        </ResponsiveContainer>
        <div className="flex justify-between mt-1 text-xs text-stone-400">
          <span>{plot.x_label}</span>
          <span>{plot.y_label}</span>
        </div>
      </div>
    </div>
  );
}
