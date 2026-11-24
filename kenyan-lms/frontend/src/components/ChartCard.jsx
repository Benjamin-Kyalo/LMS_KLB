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

const CHART_COLOURS = ["#0B3D2E", "#1C5D7E", "#8A5A15", "#4E8A6D", "#A9BBAF"];

function ChartBody({ type, data, xKey, series }) {
  if (type === "pie") {
    return (
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="label" innerRadius="35%" outerRadius="70%" paddingAngle={2}>
          {data.map((entry, index) => (
            <Cell key={entry.label || entry.status || index} fill={CHART_COLOURS[index % CHART_COLOURS.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    );
  }

  const Chart = type === "line" ? LineChart : BarChart;
  return (
    <Chart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
      <CartesianGrid strokeDasharray="3 3" stroke="#DDE3DC" vertical={false} />
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
            stroke={item.colour || CHART_COLOURS[index % CHART_COLOURS.length]}
            strokeWidth={2}
            dot={{ r: 2 }}
            connectNulls
          />
        ) : (
          <Bar
            key={item.key}
            dataKey={item.key}
            name={item.label || item.key}
            fill={item.colour || CHART_COLOURS[index % CHART_COLOURS.length]}
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
  const hasData = data.length > 0;
  return (
    <section className="panel panel-pad chart-card" aria-label={title}>
      <h3>{title}</h3>
      {subtitle && <p className="muted chart-subtitle">{subtitle}</p>}
      <div className="chart-wrap">
        {hasData ? (
          <ResponsiveContainer width="100%" height="100%">
            <ChartBody type={type} data={data} xKey={xKey} series={series} />
          </ResponsiveContainer>
        ) : (
          <div className="chart-empty">{emptyText}</div>
        )}
      </div>
    </section>
  );
}
