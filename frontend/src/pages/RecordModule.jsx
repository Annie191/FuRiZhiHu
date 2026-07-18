import { Check, Pencil, RefreshCw, Search, Trash2, X } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { createRecord, deleteRecord, getDailySummary, getFoods, listRecords, updateRecord } from '../api/member3Api.js';
import { ChartPanel, SimpleBarChart, SimpleLineChart } from '../components/charts.jsx';
import DateRangeControls from '../components/DateRangeControls.jsx';
import PageHeader from '../components/PageHeader.jsx';
import StatCard from '../components/StatCard.jsx';
import StateBlock from '../components/StateBlock.jsx';
import StatusPill from '../components/StatusPill.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { addDays, recentRange, shortDate, todayIso } from '../utils/date.js';

const mealLabels = {
  breakfast: '早餐',
  lunch: '午餐',
  dinner: '晚餐',
  snack: '加餐',
};

const sourceLabels = {
  water: '白水',
  tea: '茶饮',
  soup: '汤水',
  other: '其他',
};

const intensityLabels = {
  low: '低强度',
  medium: '中强度',
  high: '高强度',
};

const configs = {
  water: {
    eyebrow: 'Water',
    title: '饮水记录',
    description: '饮水量、来源、饮水时间',
    summaryTitle: '饮水趋势',
    columns: ['时间', '来源', '饮水量', '备注'],
    chart: (data) => (
      <SimpleBarChart
        data={data}
        xKey="label"
        bars={[
          { key: 'totalWaterMl', name: '饮水 ml', color: '#2f6fbd' },
          { key: 'drinkTimes', name: '次数', color: '#0f766e' },
        ]}
      />
    ),
  },
  food: {
    eyebrow: 'Food',
    title: '饮食记录',
    description: '餐次、食物、摄入量',
    summaryTitle: '营养趋势',
    columns: ['日期', '餐次', '食物', '摄入量', '备注'],
    chart: (data) => (
      <SimpleLineChart
        data={data}
        xKey="label"
        lines={[
          { key: 'totalCalorieKcal', name: '热量 kcal', color: '#c85f47' },
          { key: 'totalProteinG', name: '蛋白 g', color: '#3f8f5f' },
          { key: 'foodHealthScore', name: '饮食评分', color: '#0f766e' },
        ]}
      />
    ),
  },
  sport: {
    eyebrow: 'Sport',
    title: '运动记录',
    description: '运动类型、强度、时长和消耗',
    summaryTitle: '运动趋势',
    columns: ['日期', '类型', '强度', '时长', '消耗', '备注'],
    chart: (data) => (
      <SimpleBarChart
        data={data}
        xKey="label"
        bars={[
          { key: 'totalDurationMin', name: '时长 min', color: '#3f8f5f' },
          { key: 'totalCaloriesBurned', name: '消耗 kcal', color: '#c85f47' },
        ]}
      />
    ),
  },
  sleep: {
    eyebrow: 'Sleep',
    title: '睡眠记录',
    description: '入睡、醒来、睡眠质量',
    summaryTitle: '睡眠趋势',
    columns: ['记录日', '入睡', '醒来', '质量评分', '备注'],
    chart: (data) => (
      <SimpleLineChart
        data={data}
        xKey="label"
        lines={[
          { key: 'sleepHours', name: '睡眠小时', color: '#7461a8' },
          { key: 'sleepQualityScore', name: '质量评分', color: '#0f766e' },
        ]}
      />
    ),
  },
};

function defaultForm(kind, date = todayIso()) {
  if (kind === 'water') {
    return { amountMl: 300, source: 'water', date, time: '09:00', note: '' };
  }
  if (kind === 'food') {
    return { foodId: '', mealType: 'breakfast', amount: 100, amountUnit: 'g', intakeDate: date, note: '' };
  }
  if (kind === 'sport') {
    return { sportType: '快走', intensity: 'medium', durationMin: 30, caloriesBurned: 120, recordDate: date, startTime: '18:30', note: '' };
  }
  return {
    sleepDate: addDays(date, -1),
    sleepTime: '22:30',
    wakeDate: date,
    wakeTime: '07:00',
    qualityScore: 80,
    note: '',
  };
}

function compactPayload(payload) {
  return Object.fromEntries(Object.entries(payload).filter(([, value]) => value !== '' && value !== null && value !== undefined));
}

function buildPayload(kind, form, foods) {
  if (kind === 'water') {
    return compactPayload({
      amountMl: Number(form.amountMl),
      source: form.source,
      intakeTime: `${form.date} ${form.time}:00`,
      note: form.note,
    });
  }

  if (kind === 'food') {
    const selectedFood = foods.find((item) => String(item.id) === String(form.foodId));
    const amountUnit = selectedFood ? (selectedFood.unitBasis === 'per_100ml' ? 'ml' : 'g') : form.amountUnit || 'g';
    return compactPayload({
      foodId: Number(form.foodId),
      mealType: form.mealType,
      amount: Number(form.amount),
      amountUnit,
      intakeDate: form.intakeDate,
      note: form.note,
    });
  }

  if (kind === 'sport') {
    return compactPayload({
      sportType: form.sportType,
      intensity: form.intensity,
      durationMin: Number(form.durationMin),
      caloriesBurned: Number(form.caloriesBurned),
      recordDate: form.recordDate,
      startTime: form.startTime ? `${form.startTime}:00` : '',
      note: form.note,
    });
  }

  return compactPayload({
    sleepTime: `${form.sleepDate} ${form.sleepTime}:00`,
    wakeTime: `${form.wakeDate} ${form.wakeTime}:00`,
    qualityScore: Number(form.qualityScore),
    recordDate: form.wakeDate,
    note: form.note,
  });
}

function formFromRecord(kind, record) {
  if (kind === 'water') {
    return {
      amountMl: record.amountMl,
      source: record.source,
      date: record.intakeTime.slice(0, 10),
      time: record.intakeTime.slice(11, 16),
      note: record.note || '',
    };
  }
  if (kind === 'food') {
    return {
      foodId: String(record.foodId),
      mealType: record.mealType,
      amount: record.amount,
      amountUnit: record.amountUnit,
      intakeDate: record.intakeDate,
      note: record.note || '',
    };
  }
  if (kind === 'sport') {
    return {
      sportType: record.sportType,
      intensity: record.intensity,
      durationMin: record.durationMin,
      caloriesBurned: record.caloriesBurned,
      recordDate: record.recordDate,
      startTime: record.startTime ? record.startTime.slice(0, 5) : '',
      note: record.note || '',
    };
  }
  return {
    sleepDate: record.sleepTime.slice(0, 10),
    sleepTime: record.sleepTime.slice(11, 16),
    wakeDate: record.wakeTime.slice(0, 10),
    wakeTime: record.wakeTime.slice(11, 16),
    qualityScore: record.qualityScore,
    note: record.note || '',
  };
}

function summaryStats(kind, summaries, records) {
  const count = summaries.length || 1;
  if (kind === 'water') {
    const total = summaries.reduce((sum, item) => sum + item.totalWaterMl, 0);
    const times = summaries.reduce((sum, item) => sum + item.drinkTimes, 0);
    return [
      { label: '累计饮水', value: `${Math.round(total)}ml`, hint: `日均 ${Math.round(total / count)}ml`, tone: 'blue' },
      { label: '饮水次数', value: `${times}次`, hint: `${records.length} 条明细`, tone: 'teal' },
      { label: '记录天数', value: `${summaries.length}天`, hint: '按有记录日期统计', tone: 'neutral' },
    ];
  }
  if (kind === 'food') {
    const calorie = summaries.reduce((sum, item) => sum + item.totalCalorieKcal, 0);
    const protein = summaries.reduce((sum, item) => sum + item.totalProteinG, 0);
    const score = summaries.reduce((sum, item) => sum + item.foodHealthScore, 0);
    return [
      { label: '累计热量', value: `${Math.round(calorie)}kcal`, hint: `日均 ${Math.round(calorie / count)}kcal`, tone: 'coral' },
      { label: '累计蛋白', value: `${protein.toFixed(1)}g`, hint: `日均 ${(protein / count).toFixed(1)}g`, tone: 'green' },
      { label: '平均饮食评分', value: (score / count).toFixed(1), hint: `${records.length} 条明细`, tone: 'teal' },
    ];
  }
  if (kind === 'sport') {
    const duration = summaries.reduce((sum, item) => sum + item.totalDurationMin, 0);
    const calories = summaries.reduce((sum, item) => sum + item.totalCaloriesBurned, 0);
    const times = summaries.reduce((sum, item) => sum + item.sportTimes, 0);
    return [
      { label: '累计运动', value: `${Math.round(duration)}min`, hint: `日均 ${Math.round(duration / count)}min`, tone: 'green' },
      { label: '累计消耗', value: `${Math.round(calories)}kcal`, hint: `${times} 次运动`, tone: 'coral' },
      { label: '活跃天数', value: `${summaries.length}天`, hint: `${records.length} 条明细`, tone: 'teal' },
    ];
  }
  const hours = summaries.reduce((sum, item) => sum + item.sleepHours, 0);
  const score = summaries.reduce((sum, item) => sum + item.sleepQualityScore, 0);
  return [
    { label: '平均睡眠', value: `${(hours / count).toFixed(1)}h`, hint: `${summaries.length} 个睡眠日`, tone: 'violet' },
    { label: '平均质量', value: (score / count).toFixed(1), hint: '质量评分均值', tone: 'teal' },
    { label: '记录明细', value: `${records.length}条`, hint: '可编辑或删除', tone: 'neutral' },
  ];
}

function round(value, digits = 2) {
  return Number(value.toFixed(digits));
}

function hoursBetween(start, end) {
  const startTime = new Date(start.replace(' ', 'T')).getTime();
  const endTime = new Date(end.replace(' ', 'T')).getTime();
  if (Number.isNaN(startTime) || Number.isNaN(endTime)) return 0;
  return Math.max(0, (endTime - startTime) / 36e5);
}

function scoreFoodDay(item) {
  const calorieScore = item.totalCalorieKcal >= 1200 && item.totalCalorieKcal <= 2200 ? 100 : item.totalCalorieKcal >= 900 && item.totalCalorieKcal <= 2600 ? 80 : 60;
  const proteinScore = item.totalProteinG >= 60 ? 100 : item.totalProteinG >= 40 ? 80 : 60;
  const waterScore = item.totalFoodWaterMl >= 800 ? 100 : item.totalFoodWaterMl >= 500 ? 80 : 60;
  return round((calorieScore + proteinScore + waterScore) / 3);
}

function buildFallbackSummaries(kind, records) {
  const byDate = new Map();
  const ensure = (date, seed) => {
    if (!byDate.has(date)) byDate.set(date, { date, ...seed });
    return byDate.get(date);
  };

  records.forEach((record) => {
    if (kind === 'water') {
      const item = ensure(record.intakeTime.slice(0, 10), { totalWaterMl: 0, drinkTimes: 0 });
      item.totalWaterMl += Number(record.amountMl) || 0;
      item.drinkTimes += 1;
      return;
    }

    if (kind === 'food') {
      const item = ensure(record.intakeDate, { totalCalorieKcal: 0, totalProteinG: 0, totalFoodWaterMl: 0, foodHealthScore: 0 });
      const amount = Number(record.amount) || 0;
      item.totalCalorieKcal += ((Number(record.food?.calorieKcal) || 0) * amount) / 100;
      item.totalProteinG += ((Number(record.food?.proteinG) || 0) * amount) / 100;
      item.totalFoodWaterMl += ((Number(record.food?.waterMl) || 0) * amount) / 100;
      return;
    }

    if (kind === 'sport') {
      const item = ensure(record.recordDate, { totalDurationMin: 0, totalCaloriesBurned: 0, sportTimes: 0 });
      item.totalDurationMin += Number(record.durationMin) || 0;
      item.totalCaloriesBurned += Number(record.caloriesBurned) || 0;
      item.sportTimes += 1;
      return;
    }

    const item = ensure(record.recordDate, { sleepHours: 0, sleepQualityScore: 0, sleepTimes: 0 });
    item.sleepHours += hoursBetween(record.sleepTime, record.wakeTime);
    item.sleepQualityScore += Number(record.qualityScore) || 0;
    item.sleepTimes += 1;
  });

  return Array.from(byDate.values())
    .map((item) => {
      if (kind === 'food') {
        const next = {
          ...item,
          totalCalorieKcal: round(item.totalCalorieKcal),
          totalProteinG: round(item.totalProteinG),
          totalFoodWaterMl: round(item.totalFoodWaterMl),
        };
        return { ...next, foodHealthScore: scoreFoodDay(next) };
      }
      if (kind === 'sport') {
        return { ...item, totalCaloriesBurned: round(item.totalCaloriesBurned) };
      }
      if (kind === 'sleep') {
        return {
          date: item.date,
          sleepHours: round(item.sleepHours / item.sleepTimes),
          sleepQualityScore: round(item.sleepQualityScore / item.sleepTimes),
        };
      }
      return item;
    })
    .sort((a, b) => a.date.localeCompare(b.date));
}

function renderRecordCells(kind, record) {
  if (kind === 'water') {
    return [record.intakeTime, sourceLabels[record.source] || record.source, `${record.amountMl}ml`, record.note || '-'];
  }
  if (kind === 'food') {
    return [record.intakeDate, mealLabels[record.mealType] || record.mealType, record.food?.name || record.foodId, `${record.amount}${record.amountUnit}`, record.note || '-'];
  }
  if (kind === 'sport') {
    return [record.recordDate, record.sportType, intensityLabels[record.intensity] || record.intensity, `${record.durationMin}min`, `${record.caloriesBurned}kcal`, record.note || '-'];
  }
  return [record.recordDate, record.sleepTime, record.wakeTime, `${record.qualityScore}分`, record.note || '-'];
}

export default function RecordModule({ kind }) {
  const config = configs[kind];
  const { token, user } = useAuth();
  const initialRange = useMemo(() => recentRange(7), []);
  const [from, setFrom] = useState(initialRange.from);
  const [to, setTo] = useState(initialRange.to);
  const [summaries, setSummaries] = useState([]);
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(() => defaultForm(kind, initialRange.to));
  const [foods, setFoods] = useState([]);
  const [foodQuery, setFoodQuery] = useState('');
  const [foodError, setFoodError] = useState('');

  const loadData = useCallback(() => {
    if (!token) return Promise.resolve();
    setLoading(true);
    setError('');
    return Promise.allSettled([
      getDailySummary(token, kind, { from, to }),
      listRecords(token, kind, { from, to, pageSize: 50 }),
    ])
      .then(([summaryResult, recordResult]) => {
        if (recordResult.status === 'rejected' && summaryResult.status === 'rejected') {
          throw recordResult.reason;
        }

        const nextRecords = recordResult.status === 'fulfilled' ? recordResult.value?.items || [] : [];
        const nextSummaries = summaryResult.status === 'fulfilled' ? summaryResult.value || [] : buildFallbackSummaries(kind, nextRecords);

        setSummaries(nextSummaries);
        setRecords(nextRecords);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [from, kind, to, token]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (kind !== 'food') return undefined;
    let ignore = false;
    setFoodError('');
    getFoods({ q: foodQuery || undefined, pageSize: 50 })
      .then((data) => {
        if (ignore) return;
        const items = data.items || [];
        setFoods(items);
        setForm((current) => (current.foodId || !items[0] ? current : { ...current, foodId: String(items[0].id), amountUnit: items[0].unitBasis === 'per_100ml' ? 'ml' : 'g' }));
      })
      .catch((err) => {
        if (!ignore) setFoodError(err.message);
      });
    return () => {
      ignore = true;
    };
  }, [foodQuery, kind]);

  const chartData = summaries.map((item) => ({ ...item, label: shortDate(item.date) }));
  const stats = summaryStats(kind, summaries, records);

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError('');
    try {
      const payload = buildPayload(kind, form, foods);
      if (editingId) {
        await updateRecord(token, kind, editingId, payload);
      } else {
        await createRecord(token, kind, payload);
      }
      setEditingId(null);
      setForm(defaultForm(kind, to));
      await loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(recordId) {
    setError('');
    try {
      await deleteRecord(token, kind, recordId);
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  }

  function startEdit(record) {
    setEditingId(record.id);
    setForm(formFromRecord(kind, record));
  }

  function cancelEdit() {
    setEditingId(null);
    setForm(defaultForm(kind, to));
  }

  return (
    <section className="wide-page">
      <PageHeader
        eyebrow={config.eyebrow}
        title={config.title}
        actions={
          <>
            <DateRangeControls from={from} to={to} onFromChange={setFrom} onToChange={setTo} />
            <button className="icon-button" type="button" onClick={loadData} aria-label="刷新记录">
              <RefreshCw size={18} />
            </button>
          </>
        }
      />

      <StateBlock loading={loading} error={error} empty={!user}>
        <div className="stat-grid">
          {stats.map((item) => (
            <StatCard key={item.label} {...item} />
          ))}
        </div>

        <div className="record-grid">
          <article className="form-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">{editingId ? 'Edit' : 'Create'}</p>
                <h2>{editingId ? '编辑记录' : '新增记录'}</h2>
              </div>
              {editingId ? <StatusPill tone="info">#{editingId}</StatusPill> : null}
            </div>
            {kind === 'food' ? (
              <div className="food-search">
                <label>
                  <span>食物搜索</span>
                  <div className="input-with-icon">
                    <Search size={16} />
                    <input value={foodQuery} onChange={(event) => setFoodQuery(event.target.value)} placeholder="输入食物名称" />
                  </div>
                </label>
                {foodError ? <div className="state-banner error compact">{foodError}</div> : null}
              </div>
            ) : null}
            <form className="record-form" onSubmit={handleSubmit}>
              <div className="form-grid">{renderFields(kind, form, setField, foods)}</div>
              <label className="full-field">
                <span>备注</span>
                <textarea value={form.note} onChange={(event) => setField('note', event.target.value)} rows={3} placeholder="可选" />
              </label>
              <div className="form-actions">
                <button className="primary-button" type="submit" disabled={saving || (kind === 'food' && !form.foodId)}>
                  <Check size={17} />
                  <span>{saving ? '保存中' : editingId ? '保存修改' : '新增记录'}</span>
                </button>
                {editingId ? (
                  <button className="ghost-button" type="button" onClick={cancelEdit}>
                    <X size={17} />
                    <span>取消编辑</span>
                  </button>
                ) : null}
              </div>
            </form>
          </article>

          <ChartPanel title={config.summaryTitle} subtitle="Summary">
            {chartData.length ? config.chart(chartData) : <div className="empty-chart">当前范围暂无汇总</div>}
          </ChartPanel>
        </div>

        <article className="table-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Detail</p>
              <h2>{config.description}</h2>
            </div>
            <StatusPill tone="neutral">{records.length} 条</StatusPill>
          </div>
          {records.length ? (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    {config.columns.map((column) => (
                      <th key={column}>{column}</th>
                    ))}
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map((record) => (
                    <tr key={record.id}>
                      {renderRecordCells(kind, record).map((cell, index) => (
                        <td key={`${record.id}-${index}`}>{cell}</td>
                      ))}
                      <td>
                        <div className="row-actions">
                          <button className="small-icon-button" type="button" onClick={() => startEdit(record)} aria-label="编辑记录">
                            <Pencil size={15} />
                          </button>
                          <button className="small-icon-button danger" type="button" onClick={() => handleDelete(record.id)} aria-label="删除记录">
                            <Trash2 size={15} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-block">当前范围暂无记录明细</div>
          )}
        </article>
      </StateBlock>
    </section>
  );
}

function renderFields(kind, form, setField, foods) {
  if (kind === 'water') {
    return (
      <>
        <label>
          <span>饮水量 ml</span>
          <input type="number" min="50" max="3000" value={form.amountMl} onChange={(event) => setField('amountMl', event.target.value)} />
        </label>
        <label>
          <span>来源</span>
          <select value={form.source} onChange={(event) => setField('source', event.target.value)}>
            {Object.entries(sourceLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>日期</span>
          <input type="date" value={form.date} onChange={(event) => setField('date', event.target.value)} />
        </label>
        <label>
          <span>时间</span>
          <input type="time" value={form.time} onChange={(event) => setField('time', event.target.value)} />
        </label>
      </>
    );
  }

  if (kind === 'food') {
    const selectedFood = foods.find((item) => String(item.id) === String(form.foodId));
    const amountUnit = selectedFood ? (selectedFood.unitBasis === 'per_100ml' ? 'ml' : 'g') : form.amountUnit || 'g';
    return (
      <>
        <label>
          <span>食物</span>
          <select
            value={form.foodId}
            onChange={(event) => {
              const nextFood = foods.find((item) => String(item.id) === event.target.value);
              setField('foodId', event.target.value);
              setField('amountUnit', nextFood?.unitBasis === 'per_100ml' ? 'ml' : 'g');
            }}
          >
            {foods.map((food) => (
              <option key={food.id} value={food.id}>
                {food.name} · {food.unitBasis === 'per_100ml' ? '每100ml' : '每100g'}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>餐次</span>
          <select value={form.mealType} onChange={(event) => setField('mealType', event.target.value)}>
            {Object.entries(mealLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>摄入量 {amountUnit}</span>
          <input type="number" min="1" max="10000" step="0.1" value={form.amount} onChange={(event) => setField('amount', event.target.value)} />
        </label>
        <label>
          <span>日期</span>
          <input type="date" value={form.intakeDate} onChange={(event) => setField('intakeDate', event.target.value)} />
        </label>
      </>
    );
  }

  if (kind === 'sport') {
    return (
      <>
        <label>
          <span>运动类型</span>
          <input value={form.sportType} onChange={(event) => setField('sportType', event.target.value)} />
        </label>
        <label>
          <span>强度</span>
          <select value={form.intensity} onChange={(event) => setField('intensity', event.target.value)}>
            {Object.entries(intensityLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>时长 min</span>
          <input type="number" min="1" max="1440" value={form.durationMin} onChange={(event) => setField('durationMin', event.target.value)} />
        </label>
        <label>
          <span>消耗 kcal</span>
          <input type="number" min="0" max="20000" step="0.1" value={form.caloriesBurned} onChange={(event) => setField('caloriesBurned', event.target.value)} />
        </label>
        <label>
          <span>日期</span>
          <input type="date" value={form.recordDate} onChange={(event) => setField('recordDate', event.target.value)} />
        </label>
        <label>
          <span>开始时间</span>
          <input type="time" value={form.startTime} onChange={(event) => setField('startTime', event.target.value)} />
        </label>
      </>
    );
  }

  return (
    <>
      <label>
        <span>入睡日期</span>
        <input type="date" value={form.sleepDate} onChange={(event) => setField('sleepDate', event.target.value)} />
      </label>
      <label>
        <span>入睡时间</span>
        <input type="time" value={form.sleepTime} onChange={(event) => setField('sleepTime', event.target.value)} />
      </label>
      <label>
        <span>醒来日期</span>
        <input type="date" value={form.wakeDate} onChange={(event) => setField('wakeDate', event.target.value)} />
      </label>
      <label>
        <span>醒来时间</span>
        <input type="time" value={form.wakeTime} onChange={(event) => setField('wakeTime', event.target.value)} />
      </label>
      <label>
        <span>质量评分</span>
        <input type="number" min="0" max="100" value={form.qualityScore} onChange={(event) => setField('qualityScore', event.target.value)} />
      </label>
    </>
  );
}
