import { CalendarCheck, RefreshCw } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { getPlans } from '../api/fucareApi.js';
import { ChartPanel, SimpleBarChart } from '../components/charts.jsx';
import DateRangeControls from '../components/DateRangeControls.jsx';
import PageHeader from '../components/PageHeader.jsx';
import StatCard from '../components/StatCard.jsx';
import StateBlock from '../components/StateBlock.jsx';
import StatusPill from '../components/StatusPill.jsx';
import UserSelect from '../components/UserSelect.jsx';
import useAnalyticsUsers from '../hooks/useAnalyticsUsers.js';
import { recentRange, shortDate } from '../utils/date.js';

export default function Plan() {
  const { users, selectedUserId, setSelectedUserId, loadingUsers, userError } = useAnalyticsUsers();
  const initialRange = useMemo(() => recentRange(7), []);
  const [from, setFrom] = useState(initialRange.from);
  const [to, setTo] = useState(initialRange.to);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  function loadPlans() {
    if (!selectedUserId) return;
    setLoading(true);
    setError('');
    getPlans(selectedUserId, { from, to })
      .then((data) => setPlans(data.items || []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadPlans();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [from, selectedUserId, to]);

  const completed = plans.filter((item) => item.status === 'completed').length;
  const avgTarget = plans.length ? plans.reduce((sum, item) => sum + item.healthTargetScore, 0) / plans.length : 0;
  const chartData = plans
    .slice()
    .reverse()
    .map((item) => ({
      ...item,
      label: shortDate(item.date),
      completed: item.status === 'completed' ? 1 : 0,
    }));

  return (
    <section className="wide-page">
      <PageHeader
        eyebrow="Daily Plan"
        title="养生计划"
        actions={
          <>
            <UserSelect users={users} value={selectedUserId} onChange={setSelectedUserId} disabled={loadingUsers} />
            <DateRangeControls from={from} to={to} onFromChange={setFrom} onToChange={setTo} />
            <button className="icon-button" type="button" onClick={loadPlans} aria-label="刷新计划">
              <RefreshCw size={18} />
            </button>
          </>
        }
      />

      <StateBlock loading={loadingUsers || loading} error={userError || error} empty={!selectedUserId}>
        <div className="stat-grid">
          <StatCard label="计划天数" value={`${plans.length}天`} hint={`${from} 至 ${to}`} tone="teal" />
          <StatCard label="已完成" value={`${completed}天`} hint={`完成率 ${plans.length ? Math.round((completed / plans.length) * 100) : 0}%`} tone="green" />
          <StatCard label="平均目标" value={`${avgTarget.toFixed(1)}分`} hint="健康指数目标" tone="blue" />
        </div>

        <div className="section-grid">
          <ChartPanel title="计划目标" subtitle="Target">
            {chartData.length ? (
              <SimpleBarChart
                data={chartData}
                xKey="label"
                bars={[
                  { key: 'healthTargetScore', name: '目标分', color: '#0f766e' },
                  { key: 'completed', name: '完成', color: '#3f8f5f' },
                ]}
              />
            ) : (
              <div className="empty-chart">当前范围暂无计划</div>
            )}
          </ChartPanel>

          <article className="table-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">List</p>
                <h2>计划明细</h2>
              </div>
              <CalendarCheck size={20} />
            </div>
            {plans.length ? (
              <div className="plan-cards">
                {plans.map((plan) => (
                  <article className="plan-card" key={plan.id}>
                    <div className="plan-card-head">
                      <strong>{plan.date}</strong>
                      <StatusPill tone={plan.status === 'completed' ? 'success' : 'info'}>
                        {plan.status === 'completed' ? '已完成' : '待执行'}
                      </StatusPill>
                      <span>目标 {plan.healthTargetScore} 分</span>
                    </div>
                    <div className="plan-step-grid">
                      <PlanBlock title="早餐" text={plan.breakfastAdvice} />
                      <PlanBlock title="午间" text={plan.middayAdvice} />
                      <PlanBlock title="运动" text={plan.exerciseAdvice} />
                      <PlanBlock title="晚间" text={plan.eveningAdvice} />
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="empty-block">当前范围暂无计划数据</div>
            )}
          </article>
        </div>
      </StateBlock>
    </section>
  );
}

function PlanBlock({ title, text }) {
  return (
    <article className="plan-block">
      <span>{title}</span>
      <p>{text}</p>
    </article>
  );
}
