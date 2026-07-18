import { RefreshCw } from 'lucide-react';
import { useEffect, useState } from 'react';

import { getDashboardSeries, getHealthScoreTrend, getTrendSummary } from '../api/fucareApi.js';
import { ChartPanel, SimpleBarChart, SimpleLineChart } from '../components/charts.jsx';
import PageHeader from '../components/PageHeader.jsx';
import StatCard from '../components/StatCard.jsx';
import StateBlock from '../components/StateBlock.jsx';
import UserSelect from '../components/UserSelect.jsx';
import useAnalyticsUsers from '../hooks/useAnalyticsUsers.js';
import { addDays, shortDate, todayIso } from '../utils/date.js';

export default function Trends() {
  const { users, selectedUserId, setSelectedUserId, loadingUsers, userError } = useAnalyticsUsers();
  const [days, setDays] = useState(30);
  const [trend, setTrend] = useState(null);
  const [summary, setSummary] = useState(null);
  const [series, setSeries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  function loadTrends() {
    if (!selectedUserId) return;
    const end = todayIso();
    const start = addDays(end, -Number(days));
    setLoading(true);
    setError('');
    Promise.all([
      getHealthScoreTrend(selectedUserId, Number(days)),
      getTrendSummary(selectedUserId, Number(days)),
      getDashboardSeries(selectedUserId, { from: start, to: end }),
    ])
      .then(([trendData, summaryData, seriesData]) => {
        setTrend(trendData);
        setSummary(summaryData);
        setSeries(seriesData.items || []);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadTrends();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days, selectedUserId]);

  const scoreData = trend?.chart_data?.map((item) => ({ ...item, label: shortDate(item.date) })) || [];
  const seriesData = series.map((item) => ({ ...item, label: shortDate(item.date) }));

  return (
    <section className="wide-page">
      <PageHeader
        eyebrow="Trends"
        title="健康趋势分析"
        actions={
          <>
            <UserSelect users={users} value={selectedUserId} onChange={setSelectedUserId} disabled={loadingUsers} />
            <label>
              <span>周期</span>
              <select value={days} onChange={(event) => setDays(event.target.value)}>
                <option value={7}>近 7 天</option>
                <option value={14}>近 14 天</option>
                <option value={30}>近 30 天</option>
                <option value={60}>近 60 天</option>
                <option value={90}>近 90 天</option>
              </select>
            </label>
            <button className="icon-button" type="button" onClick={loadTrends} aria-label="刷新趋势">
              <RefreshCw size={18} />
            </button>
          </>
        }
      />

      <StateBlock loading={loadingUsers || loading} error={userError || error} empty={!trend}>
        <div className="stat-grid">
          <StatCard label="当前指数" value={trend?.current || 0} hint={trend?.trend || '趋势'} tone="teal" />
          <StatCard label="周期均值" value={trend?.avg || 0} hint={`变化 ${trend?.change || '0.0'}`} tone="blue" />
          <StatCard label="最高 / 最低" value={`${trend?.max || 0} / ${trend?.min || 0}`} hint={`${trend?.days || days} 天`} tone="green" />
          <StatCard label="睡眠均值" value={`${summary?.sleep?.avg_hours || 0}h`} hint={`质量 ${summary?.sleep?.avg_quality || 0}`} tone="violet" />
        </div>

        <div className="section-grid">
          <ChartPanel title="健康指数" subtitle="Score">
            {scoreData.length ? <SimpleLineChart data={scoreData} xKey="label" lines={[{ key: 'score', name: '健康指数' }]} /> : <div className="empty-chart">当前周期暂无指数趋势</div>}
          </ChartPanel>
          <ChartPanel title="行为趋势" subtitle="Behavior">
            {seriesData.length ? (
              <SimpleBarChart
                data={seriesData}
                xKey="label"
                bars={[
                  { key: 'waterMl', name: '饮水 ml', color: '#2f6fbd' },
                  { key: 'sportDurationMin', name: '运动 min', color: '#3f8f5f' },
                  { key: 'sleepHours', name: '睡眠 h', color: '#7461a8' },
                ]}
              />
            ) : (
              <div className="empty-chart">当前周期暂无行为汇总</div>
            )}
          </ChartPanel>
          <article className="text-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Assessment</p>
                <h2>综合判断</h2>
              </div>
            </div>
            <p>{summary?.overall_assessment || '暂无趋势判断'}</p>
            <div className="trend-badges">
              <span>饮水 {summary?.water?.trend || '-'}</span>
              <span>运动 {summary?.sport?.trend || '-'}</span>
              <span>饮食 {summary?.food?.trend || '-'}</span>
              <span>睡眠 {summary?.sleep?.trend || '-'}</span>
            </div>
          </article>
        </div>
      </StateBlock>
    </section>
  );
}
