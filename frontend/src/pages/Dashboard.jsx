import { Activity, Apple, Droplets, RefreshCw, ShieldAlert, TimerReset } from 'lucide-react';
import { useEffect, useState } from 'react';

import { getHealthScoreTrend, getTrendSummary } from '../api/fucareApi.js';
import HealthScoreRing from '../components/HealthScoreRing.jsx';
import MetricCard from '../components/MetricCard.jsx';
import Sparkline from '../components/Sparkline.jsx';
import StatusPill from '../components/StatusPill.jsx';
import useDashboardResource from '../hooks/useDashboardResource.js';
import { healthImages } from '../utils/healthImages.js';

const metricConfig = [
  {
    key: 'water',
    icon: Droplets,
    title: '饮水',
    tone: 'blue',
    getValue: (item) => `${item.current_ml}ml`,
    getDetail: (item) => `目标 ${item.target_ml}ml`,
  },
  {
    key: 'sport',
    icon: Activity,
    title: '运动',
    tone: 'green',
    getValue: (item) => `${item.current_min}min`,
    getDetail: (item) => `目标 ${item.target_min}min`,
  },
  {
    key: 'food',
    icon: Apple,
    title: '饮食',
    tone: 'coral',
    getValue: (item) => `${item.food_health_score}分`,
    getDetail: () => '营养健康评分',
  },
  {
    key: 'sleep',
    icon: TimerReset,
    title: '睡眠',
    tone: 'violet',
    getValue: (item) => `${item.sleep_hours}h`,
    getDetail: (item) => `质量 ${item.quality_score}分`,
  },
];

function riskTone(risk) {
  if (risk === 'extreme') return 'danger';
  if (risk === 'high') return 'warning';
  if (risk === 'medium') return 'info';
  return 'success';
}

export default function Dashboard() {
  const {
    users,
    selectedUserId,
    setSelectedUserId,
    selectedDate,
    setSelectedDate,
    selectedCity,
    setSelectedCity,
    dashboard,
    loading,
    error,
    reload,
  } = useDashboardResource();
  const [trend, setTrend] = useState(null);
  const [summary, setSummary] = useState(null);
  const [trendError, setTrendError] = useState('');

  useEffect(() => {
    if (!selectedUserId) return;

    let ignore = false;
    setTrendError('');
    Promise.all([getHealthScoreTrend(selectedUserId, 30), getTrendSummary(selectedUserId, 30)])
      .then(([trendData, summaryData]) => {
        if (ignore) return;
        setTrend(trendData);
        setSummary(summaryData);
      })
      .catch((err) => {
        if (!ignore) setTrendError(err.message);
      });

    return () => {
      ignore = true;
    };
  }, [selectedUserId]);

  const overview = dashboard?.overview;
  const completion = overview?.task_completion || {};
  const plan = dashboard?.plan;
  const weather = dashboard?.weather;
  const availableDates =
    dashboard?.available_dates?.length > 0
      ? dashboard.available_dates
      : [dashboard?.selected_date || selectedDate].filter(Boolean);

  return (
    <div className="dashboard-page">
      <section className="dashboard-toolbar">
        <div>
          <p className="eyebrow">Dashboard</p>
          <h1>{dashboard ? `上午好，${dashboard.user.nickname}` : '健康首页'}</h1>
        </div>

        <div className="toolbar-actions">
          <label>
            <span>用户</span>
            <select
              value={selectedUserId}
              onChange={(event) => {
                const next = event.target.value;
                const user = users.find((item) => String(item.user_id) === next);
                setSelectedUserId(next);
                setSelectedDate(user?.latest_date || '');
              }}
            >
              {users.map((user) => (
                <option key={user.user_id} value={user.user_id}>
                  {user.nickname}
                </option>
              ))}
            </select>
          </label>

          <label>
            <span>日期</span>
            <select value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)}>
              {availableDates.map((date) => (
                <option key={date} value={date}>
                  {date}
                </option>
              ))}
            </select>
          </label>

          <label>
            <span>城市</span>
            <select value={selectedCity} onChange={(event) => setSelectedCity(event.target.value)}>
              {(dashboard?.available_cities || ['上海']).map((city) => (
                <option key={city} value={city}>
                  {city}
                </option>
              ))}
            </select>
          </label>

          <button className="icon-button" type="button" onClick={reload} aria-label="刷新数据">
            <RefreshCw size={18} />
          </button>
        </div>
      </section>

      {error ? <div className="state-banner error">{error}</div> : null}
      {loading && !dashboard ? <div className="state-banner">正在加载健康数据...</div> : null}

      {dashboard && overview ? (
        <>
          <section className="dashboard-image-band">
            <img src={healthImages.redApple} alt="" />
            <div>
              <p className="eyebrow">Daily Signal</p>
              <h2>{dashboard.user.nickname}</h2>
              <span>{overview.health_score} 分 · {overview.grade}</span>
            </div>
          </section>

          <section className="hero-grid">
            <div className="score-panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">今日健康评分</p>
                  <h2>{overview.date}</h2>
                </div>
                <StatusPill tone="success">{overview.grade}</StatusPill>
              </div>
              <HealthScoreRing
                score={overview.health_score}
                grade={overview.grade}
                targetScore={plan?.health_target_score}
              />
            </div>

            <div className="weather-panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">天气环境</p>
                  <h2>{weather ? weather.city : selectedCity}</h2>
                </div>
                {weather ? <StatusPill tone={riskTone(weather.heat_risk)}>{weather.heat_risk_label}</StatusPill> : null}
              </div>
              {weather ? (
                <div className="weather-content">
                  <strong>{weather.temperature_c}℃</strong>
                  <div className="weather-stats">
                    <span>湿度 {weather.humidity_pct}%</span>
                    <span>UV {weather.uv_index}</span>
                    <span>AQI {weather.air_quality_index}</span>
                  </div>
                  <p>{weather.advice}</p>
                </div>
              ) : (
                <div className="empty-block">暂无天气数据</div>
              )}
            </div>

            <div className="profile-panel">
              <img className="panel-top-image" src={healthImages.greenFruit} alt="" />
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">健康画像</p>
                  <h2>{dashboard.profile.profile_tag}</h2>
                </div>
                <ShieldAlert size={21} />
              </div>
              <dl className="profile-grid">
                <div>
                  <dt>BMI</dt>
                  <dd>{dashboard.profile.bmi}</dd>
                </div>
                <div>
                  <dt>目标</dt>
                  <dd>{dashboard.profile.goal_label}</dd>
                </div>
                <div>
                  <dt>活动</dt>
                  <dd>{dashboard.profile.activity_label}</dd>
                </div>
                <div>
                  <dt>平均睡眠</dt>
                  <dd>{dashboard.profile.avg_sleep_hours}h</dd>
                </div>
              </dl>
            </div>
          </section>

          <section className="metric-grid">
            {metricConfig.map((metric) => {
              const item = completion[metric.key] || {};
              return (
                <MetricCard
                  key={metric.key}
                  icon={metric.icon}
                  title={metric.title}
                  value={metric.getValue(item)}
                  detail={metric.getDetail(item)}
                  percent={item.percent}
                  tone={metric.tone}
                />
              );
            })}
          </section>

          <section className="lower-grid">
            <div className="plan-panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">每日养生计划</p>
                  <h2>{plan?.status === 'completed' ? '已完成计划' : '今日待执行'}</h2>
                </div>
                <StatusPill tone={plan?.status === 'completed' ? 'success' : 'info'}>
                  {plan?.status === 'completed' ? '已完成' : '待执行'}
                </StatusPill>
              </div>
              {plan ? (
                <div className="plan-list">
                  <PlanItem title="早餐" text={plan.breakfast_advice} />
                  <PlanItem title="午间" text={plan.midday_advice} />
                  <PlanItem title="运动" text={plan.exercise_advice} />
                  <PlanItem title="晚间" text={plan.evening_advice} />
                </div>
              ) : (
                <div className="empty-block">暂无计划数据</div>
              )}
            </div>

            <div className="trend-panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">健康指数趋势</p>
                  <h2>{trend?.trend || '趋势'}</h2>
                </div>
                <StatusPill tone="neutral">{trend?.change || '0.0'}</StatusPill>
              </div>
              {trendError ? <div className="state-banner error compact">{trendError}</div> : null}
              <Sparkline data={trend?.chart_data || []} />
              <div className="trend-footer">
                <span>当前 {trend?.current ?? 0}</span>
                <span>平均 {trend?.avg ?? 0}</span>
                <span>最高 {trend?.max ?? 0}</span>
                <span>最低 {trend?.min ?? 0}</span>
              </div>
              {summary?.overall_assessment ? <p className="assessment">{summary.overall_assessment}</p> : null}
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
}

function PlanItem({ title, text }) {
  return (
    <div className="plan-item">
      <span>{title}</span>
      <p>{text}</p>
    </div>
  );
}
