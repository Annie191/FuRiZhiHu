import { Check, UserRound } from 'lucide-react';
import { useEffect, useState } from 'react';

import { getProfile, updateProfile } from '../api/member3Api.js';
import PageHeader from '../components/PageHeader.jsx';
import StatCard from '../components/StatCard.jsx';
import StateBlock from '../components/StateBlock.jsx';
import StatusPill from '../components/StatusPill.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { healthImages } from '../utils/healthImages.js';

const genderLabels = { male: '男', female: '女', other: '其他' };
const goalLabels = { lose_fat: '减脂', maintain: '保持健康', gain_muscle: '增肌' };
const activityLabels = { low: '较少运动', medium: '规律运动', high: '高频运动' };

export default function Profile() {
  const { token, user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let ignore = false;
    setLoading(true);
    setError('');
    getProfile(token)
      .then((data) => {
        if (ignore) return;
        setProfile(data);
        setForm(data);
      })
      .catch((err) => {
        if (ignore) return;
        if (user?.profile) {
          setProfile(user.profile);
          setForm(user.profile);
          setError('');
          return;
        }
        setError(err.message);
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });
    return () => {
      ignore = true;
    };
  }, [token]);

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError('');
    try {
      const payload = {
        age: Number(form.age),
        gender: form.gender,
        heightCm: Number(form.heightCm),
        weightKg: Number(form.weightKg),
        goal: form.goal,
        activityLevel: form.activityLevel,
        avgSleepHours: Number(form.avgSleepHours),
        waterTargetMl: Number(form.waterTargetMl),
        profileTag: form.profileTag,
      };
      const data = await updateProfile(token, payload);
      setProfile(data);
      setForm(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  const ready = Boolean(profile && form);

  return (
    <section className="wide-page">
      <PageHeader eyebrow="Profile" title="健康画像" actions={<UserRound size={24} />} />

      <StateBlock loading={loading} error={error} empty={!ready}>
        {ready ? (
          <>
            <section className="profile-hero-panel">
              <img src={healthImages.flower} alt="" />
              <div className="profile-hero-copy">
                <p className="eyebrow">Member Profile</p>
                <h1>{user?.nickname || user?.username}</h1>
                <div className="profile-hero-metrics">
                  <span>{profile.profileTag}</span>
                  <span>BMI {profile.bmi}</span>
                  <span>{goalLabels[profile.goal] || profile.goal}</span>
                </div>
              </div>
            </section>

            <div className="stat-grid">
              <StatCard label="昵称" value={user?.nickname || user?.username} hint={profile.profileTag} tone="teal" />
              <StatCard label="BMI" value={profile.bmi || '-'} hint={`${profile.heightCm || 0}cm / ${profile.weightKg || 0}kg`} tone="blue" />
              <StatCard label="健康目标" value={goalLabels[profile.goal] || profile.goal} hint={activityLabels[profile.activityLevel] || profile.activityLevel} tone="green" />
              <StatCard label="饮水目标" value={`${profile.waterTargetMl || 0}ml`} hint={`睡眠目标 ${profile.avgSleepHours || 0}h`} tone="violet" />
            </div>

            <div className="detail-grid">
              <Detail label="画像标签" value={profile.profileTag} />
              <Detail label="年龄" value={`${profile.age} 岁`} />
              <Detail label="性别" value={genderLabels[profile.gender] || profile.gender} />
              <Detail label="身高" value={`${profile.heightCm} cm`} />
              <Detail label="体重" value={`${profile.weightKg} kg`} />
              <Detail label="BMI" value={profile.bmi} />
              <Detail label="健康目标" value={<StatusPill tone="success">{goalLabels[profile.goal] || profile.goal}</StatusPill>} />
              <Detail label="运动水平" value={activityLabels[profile.activityLevel] || profile.activityLevel} />
              <Detail label="饮水目标" value={`${profile.waterTargetMl} ml`} />
              <Detail label="平均睡眠" value={`${profile.avgSleepHours} h`} />
            </div>

            <article className="form-panel profile-edit-panel">
              <img className="profile-edit-image" src={healthImages.greenFruit} alt="" />
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Edit</p>
                  <h2>画像设置</h2>
                </div>
              </div>
              <form className="record-form" onSubmit={handleSubmit}>
                <div className="form-grid">
                  <label>
                    <span>年龄</span>
                    <input type="number" min="10" max="100" value={form.age} onChange={(event) => setField('age', event.target.value)} />
                  </label>
                  <label>
                    <span>性别</span>
                    <select value={form.gender} onChange={(event) => setField('gender', event.target.value)}>
                      <option value="male">男</option>
                      <option value="female">女</option>
                      <option value="other">其他</option>
                    </select>
                  </label>
                  <label>
                    <span>身高 cm</span>
                    <input type="number" min="100" max="250" step="0.1" value={form.heightCm} onChange={(event) => setField('heightCm', event.target.value)} />
                  </label>
                  <label>
                    <span>体重 kg</span>
                    <input type="number" min="20" max="300" step="0.1" value={form.weightKg} onChange={(event) => setField('weightKg', event.target.value)} />
                  </label>
                  <label>
                    <span>健康目标</span>
                    <select value={form.goal} onChange={(event) => setField('goal', event.target.value)}>
                      <option value="lose_fat">减脂</option>
                      <option value="maintain">保持健康</option>
                      <option value="gain_muscle">增肌</option>
                    </select>
                  </label>
                  <label>
                    <span>活动水平</span>
                    <select value={form.activityLevel} onChange={(event) => setField('activityLevel', event.target.value)}>
                      <option value="low">较少运动</option>
                      <option value="medium">规律运动</option>
                      <option value="high">高频运动</option>
                    </select>
                  </label>
                  <label>
                    <span>平均睡眠 h</span>
                    <input type="number" min="0" max="24" step="0.1" value={form.avgSleepHours} onChange={(event) => setField('avgSleepHours', event.target.value)} />
                  </label>
                  <label>
                    <span>饮水目标 ml</span>
                    <input type="number" min="500" max="6000" value={form.waterTargetMl} onChange={(event) => setField('waterTargetMl', event.target.value)} />
                  </label>
                  <label className="full-field">
                    <span>画像标签</span>
                    <input value={form.profileTag} onChange={(event) => setField('profileTag', event.target.value)} />
                  </label>
                </div>
                <div className="form-actions">
                  <button className="primary-button" type="submit" disabled={saving}>
                    <Check size={17} />
                    <span>{saving ? '保存中' : '保存画像'}</span>
                  </button>
                </div>
              </form>
            </article>
          </>
        ) : null}
      </StateBlock>
    </section>
  );
}

function Detail({ label, value }) {
  return (
    <article className="detail-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}
