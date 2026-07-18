import { CloudSun, RefreshCw } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { getDashboard, getWeather } from '../api/fucareApi.js';
import { ChartPanel, SimpleBarChart, SimpleLineChart } from '../components/charts.jsx';
import DateRangeControls from '../components/DateRangeControls.jsx';
import PageHeader from '../components/PageHeader.jsx';
import StatCard from '../components/StatCard.jsx';
import StateBlock from '../components/StateBlock.jsx';
import StatusPill from '../components/StatusPill.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { recentRange, shortDate } from '../utils/date.js';

function riskTone(risk) {
  if (risk === 'extreme') return 'danger';
  if (risk === 'high') return 'warning';
  if (risk === 'medium') return 'info';
  return 'success';
}

export default function Weather() {
  const { user } = useAuth();
  const initialRange = useMemo(() => recentRange(7), []);
  const [from, setFrom] = useState(initialRange.from);
  const [to, setTo] = useState(initialRange.to);
  const [city, setCity] = useState('上海');
  const [cities, setCities] = useState(['上海']);
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user?.id) return;
    let ignore = false;
    getDashboard(user.id, { date: to, city })
      .then((data) => {
        if (!ignore && data.available_cities?.length) setCities(data.available_cities);
      })
      .catch(() => undefined);
    return () => {
      ignore = true;
    };
  }, [city, to, user?.id]);

  function loadWeather() {
    setLoading(true);
    setError('');
    getWeather({ city, from, to })
      .then(setWeather)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadWeather();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [city, from, to]);

  const items = weather?.items || [];
  const chartData = items.map((item) => ({ ...item, label: shortDate(item.date) }));
  const avgTemperature = items.length ? items.reduce((sum, item) => sum + item.temperatureC, 0) / items.length : 0;
  const avgHumidity = items.length ? items.reduce((sum, item) => sum + item.humidityPct, 0) / items.length : 0;
  const maxUv = items.reduce((max, item) => Math.max(max, item.uvIndex), 0);
  const maxAqi = items.reduce((max, item) => Math.max(max, item.airQualityIndex), 0);

  return (
    <section className="wide-page">
      <PageHeader
        eyebrow="Weather"
        title="天气环境"
        actions={
          <>
            <label>
              <span>城市</span>
              <select value={city} onChange={(event) => setCity(event.target.value)}>
                {cities.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <DateRangeControls from={from} to={to} onFromChange={setFrom} onToChange={setTo} />
            <button className="icon-button" type="button" onClick={loadWeather} aria-label="刷新天气">
              <RefreshCw size={18} />
            </button>
          </>
        }
      />

      <StateBlock loading={loading} error={error} empty={!weather}>
        <div className="stat-grid">
          <StatCard label="平均温度" value={`${avgTemperature.toFixed(1)}℃`} hint={city} tone="coral" />
          <StatCard label="平均湿度" value={`${avgHumidity.toFixed(0)}%`} hint={`${from} 至 ${to}`} tone="blue" />
          <StatCard label="最高 UV" value={maxUv} hint="紫外线指数" tone="gold" />
          <StatCard label="最高 AQI" value={maxAqi} hint="空气质量指数" tone="violet" />
        </div>

        <div className="section-grid">
          <ChartPanel title="温湿度趋势" subtitle="Climate">
            {chartData.length ? (
              <SimpleLineChart
                data={chartData}
                xKey="label"
                lines={[
                  { key: 'temperatureC', name: '温度 ℃', color: '#c85f47' },
                  { key: 'humidityPct', name: '湿度 %', color: '#2f6fbd' },
                ]}
              />
            ) : (
              <div className="empty-chart">当前范围暂无天气</div>
            )}
          </ChartPanel>
          <ChartPanel title="UV 与 AQI" subtitle="Risk">
            {chartData.length ? (
              <SimpleBarChart
                data={chartData}
                xKey="label"
                bars={[
                  { key: 'uvIndex', name: 'UV', color: '#b47b23' },
                  { key: 'airQualityIndex', name: 'AQI', color: '#7461a8' },
                ]}
              />
            ) : (
              <div className="empty-chart">当前范围暂无风险指标</div>
            )}
          </ChartPanel>
          <article className="table-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Advice</p>
                <h2>每日建议</h2>
              </div>
              <CloudSun size={20} />
            </div>
            {items.length ? (
              <div className="advice-list">
                {items.map((item) => (
                  <div className="advice-row" key={item.id}>
                    <div>
                      <strong>{item.date}</strong>
                      <span>{item.temperatureC}℃ · 湿度 {item.humidityPct}% · AQI {item.airQualityIndex}</span>
                    </div>
                    <StatusPill tone={riskTone(item.heatRisk)}>{item.heatRiskLabel}</StatusPill>
                    <p>{item.advice}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-block">当前范围暂无天气建议</div>
            )}
          </article>
        </div>
      </StateBlock>
    </section>
  );
}
