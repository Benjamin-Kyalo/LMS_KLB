import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useTheme } from "../context/ThemeContext";

function ChartBody({ type, data, xKey, series, colors }) {
  if (type === "pie") {
    return (
      <PieChart accessibilityLayer>
        <Pie data={data} dataKey="value" nameKey="label" innerRadius="35%" outerRadius="70%" paddingAngle={2}>
          {data.map((entry, index) => (
            <Cell key={`${entry.label || entry.status || "slice"}-${index}`} fill={colors.chart[index % colors.chart.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    );
  }

  const Chart = type === "line" ? LineChart : BarChart;
  return (
    <Chart accessibilityLayer data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
      <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} vertical={false} />
      <XAxis dataKey={xKey} tick={{ fontSize: 11 }} interval="preserveStartEnd" />
      <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
      <Tooltip />
      {series.length > 1 && <Legend />}
      {series.map((item, index) =>
        type === "line" ? (
          <Line
            key={item.key}
            type="monotone"
            dataKey={item.key}
            name={item.label || item.key}
            stroke={item.colour || colors.chart[index % colors.chart.length]}
            strokeWidth={2}
            dot={{ r: 2 }}
            connectNulls
          />
        ) : (
          <Bar
            key={item.key}
            dataKey={item.key}
            name={item.label || item.key}
            fill={item.colour || colors.chart[index % colors.chart.length]}
            radius={[3, 3, 0, 0]}
          />
        )
      )}
    </Chart>
  );
}

export default function ChartCard({
  title,
  subtitle,
  type = "bar",
  data = [],
  xKey = "label",
  series = [],
  emptyText = "No records to chart yet.",
}) {
  const { colors } = useTheme();
  const hasData = data.length > 0;
  const columns = type === "pie"
    ? [{ key: "value", label: "Value" }]
    : series.map((item) => ({ key: item.key, label: item.label || item.key }));
  return (
    <section className="panel panel-pad chart-card" aria-label={title}>
      <h3>{title}</h3>
      {subtitle && <p className="muted chart-subtitle">{subtitle}</p>}
      <div className="chart-wrap">
        {hasData ? (
          <ResponsiveContainer width="100%" height="100%">
            <ChartBody type={type} data={data} xKey={xKey} series={series} colors={colors} />
          </ResponsiveContainer>
        ) : (
          <div className="chart-empty">{emptyText}</div>
        )}
      </div>
      {hasData && (
        <details className="chart-data">
          <summary>View chart data</summary>
          <table>
            <caption>{title} data</caption>
            <thead>
              <tr>
                <th scope="col">{xKey === "label" ? "Label" : xKey}</th>
                {columns.map((column) => <th key={column.key} scope="col">{column.label}</th>)}
              </tr>
            </thead>
            <tbody>
              {data.map((row, index) => (
                <tr key={`${row[xKey] ?? row.label ?? "row"}-${index}`}>
                  <th scope="row">{row[xKey] ?? row.label ?? ""}</th>
                  {columns.map((column) => <td key={column.key}>{row[column.key] ?? ""}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      )}
    </section>
  );
}
