import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const gridColor = '#dfe7df';
const textColor = '#66746f';
const teal = '#0f766e';
const blue = '#2f6fbd';
const green = '#3f8f5f';
const coral = '#c85f47';
const violet = '#7461a8';

export function ChartPanel({ title, subtitle, children }) {
  return (
    <article className="chart-panel">
      <div className="panel-heading">
        <div>
          {subtitle ? <p className="eyebrow">{subtitle}</p> : null}
          <h2>{title}</h2>
        </div>
      </div>
      <div className="chart-box">{children}</div>
    </article>
  );
}

export function SimpleLineChart({ data, lines, xKey = 'date' }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 8, right: 18, left: -14, bottom: 0 }}>
        <CartesianGrid stroke={gridColor} strokeDasharray="4 4" />
        <XAxis dataKey={xKey} tick={{ fill: textColor, fontSize: 12 }} />
        <YAxis tick={{ fill: textColor, fontSize: 12 }} />
        <Tooltip />
        <Legend />
        {lines.map((line, index) => (
          <Line
            key={line.key}
            type="monotone"
            dataKey={line.key}
            name={line.name}
            stroke={line.color || [teal, blue, green, coral, violet][index % 5]}
            strokeWidth={3}
            dot={{ r: 4 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

export function SimpleBarChart({ data, bars, xKey = 'date' }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 8, right: 18, left: -14, bottom: 0 }}>
        <CartesianGrid stroke={gridColor} strokeDasharray="4 4" />
        <XAxis dataKey={xKey} tick={{ fill: textColor, fontSize: 12 }} />
        <YAxis tick={{ fill: textColor, fontSize: 12 }} />
        <Tooltip />
        <Legend />
        {bars.map((bar, index) => (
          <Bar key={bar.key} dataKey={bar.key} name={bar.name} fill={bar.color || [teal, blue, green, coral, violet][index % 5]} radius={[4, 4, 0, 0]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

export function SimpleRadarChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <RadarChart data={data} outerRadius="72%">
        <PolarGrid stroke={gridColor} />
        <PolarAngleAxis dataKey="name" tick={{ fill: textColor, fontSize: 12 }} />
        <Tooltip />
        <Radar dataKey="value" name="完成度" stroke={teal} fill={teal} fillOpacity={0.28} />
      </RadarChart>
    </ResponsiveContainer>
  );
}

export function ContributionBars({ data }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} layout="vertical" margin={{ top: 8, right: 20, left: 20, bottom: 0 }}>
        <CartesianGrid stroke={gridColor} strokeDasharray="4 4" />
        <XAxis type="number" tick={{ fill: textColor, fontSize: 12 }} />
        <YAxis dataKey="name" type="category" tick={{ fill: textColor, fontSize: 12 }} width={48} />
        <Tooltip />
        <Bar dataKey="contribution" name="评分贡献">
          {data.map((item, index) => (
            <Cell key={item.name} fill={item.color || [blue, green, coral, violet][index % 4]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
