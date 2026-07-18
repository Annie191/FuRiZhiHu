export default function StateBlock({ loading, error, empty, children }) {
  if (loading) return <div className="state-banner">正在加载数据...</div>;
  if (error) return <div className="state-banner error">{error}</div>;
  if (empty) return <div className="empty-block">暂无数据</div>;
  return children;
}
