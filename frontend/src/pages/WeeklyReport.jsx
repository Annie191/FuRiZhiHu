import { RefreshCw } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { getWeeklyReport } from '../api/fucareApi.js';
import { ChartPanel, SimpleLineChart } from '../components/charts.jsx';
import DateRangeControls from '../components/DateRangeControls.jsx';
import PageHeader from '../components/PageHeader.jsx';
import StatCard from '../components/StatCard.jsx';
import StateBlock from '../components/StateBlock.jsx';
import UserSelect from '../components/UserSelect.jsx';
import useAnalyticsUsers from '../hooks/useAnalyticsUsers.js';
import { expandDates, recentRange, shortDate, todayIso } from '../utils/date.js';

export default function WeeklyReport() {
  const { users, selectedUser, selectedUserId, setSelectedUserId, loadingUsers, userError } = useAnalyticsUsers();
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  function loadReport() {
    if (!selectedUserId) return;
    setLoading(true);
    setError('');
    getWeeklyReport(selectedUserId, { startDate: from, endDate: to })
      .then(setReport)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadReport();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [from, selectedUserId, to]);

  useEffect(() => {
    const latestDate = selectedUser?.latest_date || todayIso();
    const range = recentRange(7, latestDate);
    setFrom(range.from);
    setTo(range.to);
  }, [selectedUser?.latest_date, selectedUserId]);

  const trendData = useMemo(() => {
    if (!report?.score_trend?.length) return [];
    const dates = expandDates(report.period.start, report.score_trend.length);
    return report.score_trend.map((score, index) => ({ date: dates[index], label: shortDate(dates[index]), score }));
  }, [report]);

  const summary = report?.dimension_summary || {};

  return (
    <section className="wide-page">
      <PageHeader
        eyebrow="Weekly Report"
        title="每周健康报告"
        actions={
          <>
            <UserSelect users={users} value={selectedUserId} onChange={setSelectedUserId} disabled={loadingUsers} />
            <DateRangeControls from={from} to={to} onFromChange={setFrom} onToChange={setTo} />
            <button className="icon-button" type="button" onClick={loadReport} aria-label="刷新报告">
              <RefreshCw size={18} />
            </button>
          </>
        }
      />

      <StateBlock loading={loadingUsers || loading} error={userError || error} empty={!report}>
        <div className="stat-grid">
          <StatCard label="平均健康指数" value={report?.avg_health_score || 0} hint={`变化 ${report?.score_change || '0.0'}`} tone="teal" />
          <StatCard label="日均饮水" value={`${summary.water?.avg_ml || 0}ml`} hint={`最佳 ${summary.water?.best_day || '-'}`} tone="blue" />
          <StatCard label="累计运动" value={`${summary.sport?.total_min || 0}min`} hint={`活跃 ${summary.sport?.active_days || 0} 天`} tone="green" />
          <StatCard label="平均睡眠" value={`${summary.sleep?.avg_hours || 0}h`} hint={`质量 ${summary.sleep?.avg_quality || 0} 分`} tone="violet" />
        </div>

        <div className="section-grid">
          <ChartPanel title="健康指数走势" subtitle="Score Trend">
            {trendData.length ? <SimpleLineChart data={trendData} xKey="label" lines={[{ key: 'score', name: '健康指数' }]} /> : <div className="empty-chart">当前周期暂无趋势</div>}
          </ChartPanel>
          <article className="text-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Summary</p>
                <h2>周期总结</h2>
              </div>
            </div>
            <p>{report?.weekly_summary || '暂无总结'}</p>
            <div className="detail-grid compact-grid">
              <Detail label="饮食均分" value={summary.food?.avg_food_score || 0} />
              <Detail label="饮食最佳日" value={summary.food?.best_day || '-'} />
              <Detail label="运动最佳日" value={summary.sport?.best_day || '-'} />
              <Detail label="睡眠最佳日" value={summary.sleep?.best_day || '-'} />
            </div>
          </article>
        </div>
      </StateBlock>
    </section>
  );
}

function Detail({ label, value }) {
  return (
    <div className="inline-detail">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
