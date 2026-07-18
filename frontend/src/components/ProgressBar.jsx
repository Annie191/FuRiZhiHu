export default function ProgressBar({ value = 0, tone = 'teal' }) {
  const percent = Math.max(0, Math.min(Number(value) || 0, 100));

  return (
    <div className={`progress-track tone-${tone}`} aria-label={`完成度 ${percent}%`}>
      <span style={{ width: `${percent}%` }} />
    </div>
  );
}
