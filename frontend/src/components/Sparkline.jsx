export default function Sparkline({ data = [] }) {
  if (!data.length) {
    return <div className="empty-chart">暂无趋势数据</div>;
  }

  const width = 520;
  const height = 170;
  const padding = 16;
  const scores = data.map((item) => Number(item.score) || 0);
  const min = Math.min(...scores, 60);
  const max = Math.max(...scores, 100);
  const range = Math.max(max - min, 1);

  const points = data.map((item, index) => {
    const x = padding + (index / Math.max(data.length - 1, 1)) * (width - padding * 2);
    const y = height - padding - ((Number(item.score) - min) / range) * (height - padding * 2);
    return { x, y, item };
  });

  return (
    <svg className="sparkline" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="健康指数趋势">
      <path
        d={`M ${points.map((point) => `${point.x},${point.y}`).join(' L ')}`}
        fill="none"
        stroke="currentColor"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {points.map((point) => (
        <circle key={point.item.date} cx={point.x} cy={point.y} r="5" />
      ))}
    </svg>
  );
}
