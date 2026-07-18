import { Activity, Apple, ClipboardList, Droplets, TimerReset } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { getDashboardSeries } from '../api/fucareApi.js';
import { ChartPanel, SimpleBarChart, SimpleLineChart } from '../components/charts.jsx';
import DateRangeControls from '../components/DateRangeControls.jsx';
import PageHeader from '../components/PageHeader.jsx';
import StatCard from '../components/StatCard.jsx';
import StateBlock from '../components/StateBlock.jsx';
import UserSelect from '../components/UserSelect.jsx';
import useAnalyticsUsers from '../hooks/useAnalyticsUsers.js';
import { recentRange, shortDate } from '../utils/date.js';

const modules = [
  { to: '/records/water', title: '饮水记录', icon: Droplets, tone: 'blue', detail: '饮水量、饮水次数、来源' },
  { to: '/records/food', title: '饮食记录', icon: Apple, tone: 'coral', detail: '食物、餐次、热量和蛋白' },
  { to: '/records/sport', title: '运动记录', icon: Activity, tone: 'green', detail: '运动时长、强度和消耗' },
  { to: '/records/sleep', title: '睡眠记录', icon: TimerReset, tone: 'violet', detail: '睡眠时长和质量评分' },
];

export default function Records() {
  const { users, selectedUserId, setSelectedUserId, loadingUsers, userError } = useAnalyticsUsers();
  const initialRange = useMemo(() => recentRange(7), []);
  const [from, setFrom] = useState(initialRange.from);
  const [to, setTo] = useState(initialRange.to);
  const [series, setSeries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!selectedUserId) return;
    let ignore = false;
    setLoading(true);
    setError('');

    getDashboardSeries(selectedUserId, { from, to })
      .then((data) => {
        if (!ignore) setSeries(data.items || []);
      })
      .catch((err) => {
        if (!ignore) setError(err.message);
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });

    return () => {
      ignore = true;
    };
  }, [from, selectedUserId, to]);

  const chartData = series.map((item) => ({ ...item, label: shortDate(item.date) }));
  const totals = series.reduce(
    (result, item) => ({
      waterMl: result.waterMl + item.waterMl,
      sportDurationMin: result.sportDurationMin + item.sportDurationMin,
      foodCalorieKcal: result.foodCalorieKcal + item.foodCalorieKcal,
      sleepHours: result.sleepHours + item.sleepHours,
      healthScore: result.healthScore + item.healthScore,
    }),
    { waterMl: 0, sportDurationMin: 0, foodCalorieKcal: 0, sleepHours: 0, healthScore: 0 },
  );
  const days = series.length || 1;

  return (
    <section className="wide-page">
      <PageHeader
        eyebrow="Records"
        title="行为记录概览"
        actions={
          <>
            <UserSelect users={users} value={selectedUserId} onChange={setSelectedUserId} disabled={loadingUsers} />
            <DateRangeControls from={from} to={to} onFromChange={setFrom} onToChange={setTo} />
          </>
        }
      />

      <StateBlock loading={loadingUsers || loading} error={userError || error} empty={!selectedUserId}>
        <div className="stat-grid">
          <StatCard label="平均健康指数" value={(totals.healthScore / days).toFixed(1)} hint={`${from} 至 ${to}`} tone="teal" />
          <StatCard label="累计饮水" value={`${Math.round(totals.waterMl)}ml`} hint={`日均 ${Math.round(totals.waterMl / days)}ml`} tone="blue" />
          <StatCard label="累计运动" value={`${Math.round(totals.sportDurationMin)}min`} hint={`日均 ${Math.round(totals.sportDurationMin / days)}min`} tone="green" />
          <StatCard label="平均睡眠" value={`${(totals.sleepHours / days).toFixed(1)}h`} hint="按有汇总的日期计算" tone="violet" />
        </div>

        <div className="module-links" aria-label="行为记录模块">
          {modules.map((item) => {
            const Icon = item.icon;
            return (
              <Link className={`module-link tone-${item.tone}`} key={item.to} to={item.to}>
                <span className="module-icon">
                  <Icon size={20} />
                </span>
                <strong>{item.title}</strong>
                <small>{item.detail}</small>
              </Link>
            );
          })}
        </div>

        <div className="section-grid">
          <ChartPanel title="健康指数趋势" subtitle="Score">
            <SimpleLineChart data={chartData} xKey="label" lines={[{ key: 'healthScore', name: '健康指数' }]} />
          </ChartPanel>
          <ChartPanel title="饮水与运动" subtitle="Activity">
            <SimpleBarChart
              data={chartData}
              xKey="label"
              bars={[
                { key: 'waterMl', name: '饮水 ml', color: '#2f6fbd' },
                { key: 'sportDurationMin', name: '运动 min', color: '#3f8f5f' },
              ]}
            />
          </ChartPanel>
          <ChartPanel title="饮食与睡眠" subtitle="Balance">
            <SimpleLineChart
              data={chartData}
              xKey="label"
              lines={[
                { key: 'foodHealthScore', name: '饮食评分', color: '#c85f47' },
                { key: 'sleepQualityScore', name: '睡眠质量', color: '#7461a8' },
              ]}
            />
          </ChartPanel>
          <article className="table-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Daily</p>
                <h2>每日汇总</h2>
              </div>
              <ClipboardList size={20} />
            </div>
            {chartData.length ? (
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>日期</th>
                      <th>健康指数</th>
                      <th>饮水</th>
                      <th>运动</th>
                      <th>饮食评分</th>
                      <th>睡眠</th>
                    </tr>
                  </thead>
                  <tbody>
                    {series.map((item) => (
                      <tr key={item.date}>
                        <td>{item.date}</td>
                        <td>{item.healthScore}</td>
                        <td>{item.waterMl}ml</td>
                        <td>{item.sportDurationMin}min</td>
                        <td>{item.foodHealthScore}</td>
                        <td>{item.sleepHours}h / {item.sleepQualityScore}分</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-block">当前范围暂无记录汇总</div>
            )}
          </article>
        </div>
      </StateBlock>
    </section>
  );
}
