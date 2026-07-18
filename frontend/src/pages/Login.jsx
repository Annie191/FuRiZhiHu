import { HeartPulse, LogIn } from 'lucide-react';
import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext.jsx';
import { healthImages } from '../utils/healthImages.js';

export default function Login() {
  const { isAuthenticated, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ identifier: '', password: '' });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const from = location.state?.from?.pathname || '/dashboard';

  function updateField(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await login(form);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-panel auth-panel-visual">
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
          <img src={healthImages.grass} alt="" />
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div>
            <p className="eyebrow">Login</p>
            <h1>用户登录</h1>
          </div>

          {error ? <div className="state-banner error">{error}</div> : null}

          <label>
            <span>用户名 / 手机号 / 邮箱</span>
            <input
              value={form.identifier}
              onChange={(event) => updateField('identifier', event.target.value)}
              autoComplete="username"
              required
            />
          </label>

          <label>
            <span>密码</span>
            <input
              type="password"
              value={form.password}
              onChange={(event) => updateField('password', event.target.value)}
              autoComplete="current-password"
              required
            />
          </label>

          <button className="primary-button" type="submit" disabled={submitting}>
            <LogIn size={18} />
            <span>{submitting ? '登录中...' : '登录'}</span>
          </button>

          <p className="auth-switch">
            没有账号？ <Link to="/register">去注册</Link>
          </p>
        </form>
      </section>
    </main>
  );
}
