import { CalendarDays, RefreshCw } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { getDailyReport } from '../api/fucareApi.js';
import { ChartPanel, ContributionBars, SimpleRadarChart } from '../components/charts.jsx';
import HealthScoreRing from '../components/HealthScoreRing.jsx';
import PageHeader from '../components/PageHeader.jsx';
import StatCard from '../components/StatCard.jsx';
import StateBlock from '../components/StateBlock.jsx';
import UserSelect from '../components/UserSelect.jsx';
import useAnalyticsUsers from '../hooks/useAnalyticsUsers.js';
import { todayIso } from '../utils/date.js';

const colors = {
  water: '#2f6fbd',
  sport: '#3f8f5f',
  food: '#c85f47',
  sleep: '#7461a8',
};

export default function DailyReport() {
  const { users, selectedUserId, setSelectedUserId, loadingUsers, userError } = useAnalyticsUsers();
  const [date, setDate] = useState(todayIso());
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  function loadReport() {
    if (!selectedUserId || !date) return;
    setLoading(true);
    setError('');
    getDailyReport(selectedUserId, date)
      .then(setReport)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadReport();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [date, selectedUserId]);

  const radarData = useMemo(() => {
    const breakdown = report?.breakdown || {};
    return [
      { name: '饮水', value: breakdown.water?.completion || 0 },
      { name: '运动', value: breakdown.sport?.completion || 0 },
      { name: '饮食', value: breakdown.food?.food_health_score || 0 },
      { name: '睡眠', value: breakdown.sleep?.quality_score || 0 },
    ];
  }, [report]);

  const contributionData = useMemo(() => {
    const breakdown = report?.breakdown || {};
    return [
      { name: '饮水', contribution: Number(((breakdown.water?.completion || 0) * (breakdown.water?.weight || 0)).toFixed(1)), color: colors.water },
      { name: '运动', contribution: Number(((breakdown.sport?.completion || 0) * (breakdown.sport?.weight || 0)).toFixed(1)), color: colors.sport },
      { name: '饮食', contribution: Number(((breakdown.food?.food_health_score || 0) * (breakdown.food?.weight || 0)).toFixed(1)), color: colors.food },
      { name: '睡眠', contribution: Number(((breakdown.sleep?.quality_score || 0) * (breakdown.sleep?.weight || 0)).toFixed(1)), color: colors.sleep },
    ];
  }, [report]);

  const breakdown = report?.breakdown || {};

  return (
    <section className="wide-page">
      <PageHeader
        eyebrow="Daily Report"
        title="每日健康报告"
        actions={
          <>
            <UserSelect users={users} value={selectedUserId} onChange={setSelectedUserId} disabled={loadingUsers} />
            <label>
              <span>日期</span>
              <input type="date" value={date} onChange={(event) => setDate(event.target.value)} />
            </label>
            <button className="icon-button" type="button" onClick={loadReport} aria-label="刷新报告">
              <RefreshCw size={18} />
            </button>
          </>
        }
      />

      <StateBlock loading={loadingUsers || loading} error={userError || error} empty={!report}>
        <div className="report-grid">
          <article className="score-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Score</p>
                <h2>{report?.date}</h2>
              </div>
              <CalendarDays size={20} />
            </div>
            <HealthScoreRing score={report?.health_score} grade={report?.grade} />
          </article>
          <ChartPanel title="任务完成雷达" subtitle="Breakdown">
            <SimpleRadarChart data={radarData} />
          </ChartPanel>
          <ChartPanel title="评分贡献" subtitle="Weight">
            <ContributionBars data={contributionData} />
          </ChartPanel>
        </div>

        <div className="stat-grid">
          <StatCard label="饮水完成" value={`${breakdown.water?.completion || 0}%`} hint={`${breakdown.water?.actual || 0} / ${breakdown.water?.target || 0} ml`} tone="blue" />
          <StatCard label="运动完成" value={`${breakdown.sport?.completion || 0}%`} hint={`${breakdown.sport?.actual_min || 0} / ${breakdown.sport?.target_min || 0} min`} tone="green" />
          <StatCard label="饮食评分" value={breakdown.food?.food_health_score || 0} hint={`权重 ${Math.round((breakdown.food?.weight || 0) * 100)}%`} tone="coral" />
          <StatCard label="睡眠质量" value={breakdown.sleep?.quality_score || 0} hint={`${breakdown.sleep?.sleep_hours || 0}h`} tone="violet" />
        </div>
      </StateBlock>
    </section>
  );
}
