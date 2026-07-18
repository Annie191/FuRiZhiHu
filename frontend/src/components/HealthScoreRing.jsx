export default function HealthScoreRing({ score = 0, grade = '需改善', targetScore }) {
  const safeScore = Math.max(0, Math.min(Number(score) || 0, 100));

  return (
    <div className="score-ring-wrap">
      <div className="score-ring" style={{ '--score': `${safeScore * 3.6}deg` }}>
        <div className="score-ring-inner">
          <span className="score-number">{safeScore.toFixed(1)}</span>
          <span className="score-unit">健康指数</span>
        </div>
      </div>
      <div className="score-copy">
        <strong>{grade}</strong>
        {targetScore ? <span>目标 {targetScore} 分</span> : <span>综合任务完成分</span>}
      </div>
    </div>
  );
}
