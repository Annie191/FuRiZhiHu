import ProgressBar from './ProgressBar.jsx';

export default function MetricCard({ icon: Icon, title, value, detail, percent, tone = 'teal' }) {
  return (
    <article className={`metric-card tone-${tone}`}>
      <div className="metric-icon">{Icon ? <Icon size={20} /> : null}</div>
      <div className="metric-body">
        <span className="metric-title">{title}</span>
        <strong>{value}</strong>
        <small>{detail}</small>
        <ProgressBar value={percent} tone={tone} />
      </div>
    </article>
  );
}
