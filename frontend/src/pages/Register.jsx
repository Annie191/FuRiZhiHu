import { HeartPulse, UserPlus } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext.jsx';
import { healthImages } from '../utils/healthImages.js';

const initialForm = {
  username: '',
  password: '',
  nickname: '',
  phone: '',
  email: '',
  age: '22',
  gender: 'male',
  heightCm: '175',
  weightKg: '70',
  goal: 'lose_fat',
  activityLevel: 'low',
  avgSleepHours: '7',
  waterTargetMl: '2200',
};

const goalLabels = {
  lose_fat: '夏季减脂型用户',
  maintain: '规律养生型用户',
  gain_muscle: '力量增肌型用户',
};

export default function Register() {
  const { isAuthenticated, register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const profileTag = useMemo(() => goalLabels[form.goal] || '健康管理型用户', [form.goal]);

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  function updateField(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError('');

    const payload = {
      username: form.username,
      password: form.password,
      nickname: form.nickname,
      phone: form.phone || null,
      email: form.email || null,
      profile: {
        age: Number(form.age),
        gender: form.gender,
        heightCm: Number(form.heightCm),
        weightKg: Number(form.weightKg),
        goal: form.goal,
        activityLevel: form.activityLevel,
        avgSleepHours: Number(form.avgSleepHours),
        waterTargetMl: Number(form.waterTargetMl),
        profileTag,
      },
    };

    try {
      await register(payload);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-panel auth-panel-wide auth-panel-visual">
        <div className="auth-brand">
          <span className="brand-mark">
            <HeartPulse size={22} strokeWidth={2.4} />
          </span>
          <div>
            <strong>伏日智护</strong>
            <span>FuCare</span>
          </div>
        </div>

        <div className="auth-media">
          <img src={healthImages.flower} alt="" />
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div>
            <p className="eyebrow">Register</p>
            <h1>用户注册</h1>
          </div>

          {error ? <div className="state-banner error">{error}</div> : null}

          <div className="form-grid">
            <Field label="用户名">
              <input value={form.username} onChange={(event) => updateField('username', event.target.value)} autoComplete="username" required />
            </Field>
            <Field label="昵称">
              <input value={form.nickname} onChange={(event) => updateField('nickname', event.target.value)} autoComplete="nickname" required />
            </Field>
            <Field label="密码">
              <input
                type="password"
                value={form.password}
                onChange={(event) => updateField('password', event.target.value)}
                autoComplete="new-password"
                minLength={12}
                required
              />
            </Field>
            <Field label="手机号">
              <input value={form.phone} onChange={(event) => updateField('phone', event.target.value)} autoComplete="tel" />
            </Field>
            <Field label="邮箱">
              <input type="email" value={form.email} onChange={(event) => updateField('email', event.target.value)} autoComplete="email" />
            </Field>
            <Field label="年龄">
              <input type="number" min="10" max="100" value={form.age} onChange={(event) => updateField('age', event.target.value)} required />
            </Field>
            <Field label="性别">
              <select value={form.gender} onChange={(event) => updateField('gender', event.target.value)}>
                <option value="male">男</option>
                <option value="female">女</option>
                <option value="other">其他</option>
              </select>
            </Field>
            <Field label="身高 cm">
              <input type="number" min="100" max="250" value={form.heightCm} onChange={(event) => updateField('heightCm', event.target.value)} required />
            </Field>
            <Field label="体重 kg">
              <input type="number" min="20" max="300" value={form.weightKg} onChange={(event) => updateField('weightKg', event.target.value)} required />
            </Field>
            <Field label="健康目标">
              <select value={form.goal} onChange={(event) => updateField('goal', event.target.value)}>
                <option value="lose_fat">减脂</option>
                <option value="maintain">保持健康</option>
                <option value="gain_muscle">增肌</option>
              </select>
            </Field>
            <Field label="运动水平">
              <select value={form.activityLevel} onChange={(event) => updateField('activityLevel', event.target.value)}>
                <option value="low">较少运动</option>
                <option value="medium">规律运动</option>
                <option value="high">高频运动</option>
              </select>
            </Field>
            <Field label="平均睡眠 h">
              <input
                type="number"
                min="0"
                max="24"
                step="0.5"
                value={form.avgSleepHours}
                onChange={(event) => updateField('avgSleepHours', event.target.value)}
                required
              />
            </Field>
            <Field label="饮水目标 ml">
              <input
                type="number"
                min="500"
                max="6000"
                step="100"
                value={form.waterTargetMl}
                onChange={(event) => updateField('waterTargetMl', event.target.value)}
                required
              />
            </Field>
            <Field label="画像标签">
              <input value={profileTag} readOnly />
            </Field>
          </div>

          <button className="primary-button" type="submit" disabled={submitting}>
            <UserPlus size={18} />
            <span>{submitting ? '注册中...' : '注册并进入'}</span>
          </button>

          <p className="auth-switch">
            已有账号？ <Link to="/login">去登录</Link>
          </p>
        </form>
      </section>
    </main>
  );
}

function Field({ label, children }) {
  return (
    <label>
      <span>{label}</span>
      {children}
    </label>
  );
}
