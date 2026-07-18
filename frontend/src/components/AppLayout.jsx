import {
  Activity,
  Apple,
  BarChart3,
  CalendarCheck,
  ClipboardList,
  CloudSun,
  Droplets,
  FileText,
  HeartPulse,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquareText,
  TimerReset,
  UserRound,
} from 'lucide-react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext.jsx';

const navGroups = [
  {
    label: '工作台',
    items: [
      { to: '/dashboard', label: '首页总览', icon: LayoutDashboard },
      { to: '/profile', label: '健康画像', icon: UserRound },
      { to: '/plan', label: '养生计划', icon: CalendarCheck },
    ],
  },
  {
    label: '记录',
    items: [
      { to: '/records', label: '记录概览', icon: ClipboardList, end: true },
      { to: '/records/water', label: '饮水记录', icon: Droplets },
      { to: '/records/food', label: '饮食记录', icon: Apple },
      { to: '/records/sport', label: '运动记录', icon: Activity },
      { to: '/records/sleep', label: '睡眠记录', icon: TimerReset },
    ],
  },
  {
    label: '分析',
    items: [
      { to: '/reports/daily', label: '每日报告', icon: FileText },
      { to: '/reports/weekly', label: '每周报告', icon: BarChart3 },
      { to: '/trends', label: '趋势分析', icon: HeartPulse },
      { to: '/weather', label: '天气环境', icon: CloudSun },
      { to: '/community', label: '社区动态', icon: MessageSquareText },
    ],
  },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="侧边栏导航">
        <div className="brand">
          <span className="brand-mark">
            <HeartPulse size={22} strokeWidth={2.4} />
          </span>
          <span>
            <strong>伏日智护</strong>
            <small>FuCare</small>
          </span>
        </div>

        <nav className="side-nav">
          {navGroups.map((group) => (
            <div className="side-group" key={group.label}>
              <span className="side-group-title">{group.label}</span>
              {group.items.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink key={item.to} to={item.to} end={item.end} className="side-link">
                    <Icon size={18} />
                    <span>{item.label}</span>
                  </NavLink>
                );
              })}
            </div>
          ))}
        </nav>
      </aside>

      <div className="main-shell">
        <header className="topbar">
          <div className="topbar-title">
            <Menu size={20} />
            <span>三伏健康管理工作台</span>
          </div>
          <div className="topbar-account">
            <span>{user?.nickname || user?.username}</span>
            <button className="ghost-button" type="button" onClick={handleLogout}>
              <LogOut size={17} />
              <span>退出</span>
            </button>
          </div>
        </header>

        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
