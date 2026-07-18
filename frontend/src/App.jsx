import { Navigate, Outlet, Route, Routes } from 'react-router-dom';

import AppLayout from './components/AppLayout.jsx';
import { useAuth } from './context/AuthContext.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Community from './pages/Community.jsx';
import DailyReport from './pages/DailyReport.jsx';
import FoodRecords from './pages/FoodRecords.jsx';
import Login from './pages/Login.jsx';
import Plan from './pages/Plan.jsx';
import Profile from './pages/Profile.jsx';
import Register from './pages/Register.jsx';
import Records from './pages/Records.jsx';
import SleepRecords from './pages/SleepRecords.jsx';
import SportRecords from './pages/SportRecords.jsx';
import Trends from './pages/Trends.jsx';
import WaterRecords from './pages/WaterRecords.jsx';
import Weather from './pages/Weather.jsx';
import WeeklyReport from './pages/WeeklyReport.jsx';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route element={<RequireAuth />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/plan" element={<Plan />} />
          <Route path="/records" element={<Records />} />
          <Route path="/records/water" element={<WaterRecords />} />
          <Route path="/records/food" element={<FoodRecords />} />
          <Route path="/records/sport" element={<SportRecords />} />
          <Route path="/records/sleep" element={<SleepRecords />} />
          <Route path="/reports/daily" element={<DailyReport />} />
          <Route path="/reports/weekly" element={<WeeklyReport />} />
          <Route path="/trends" element={<Trends />} />
          <Route path="/weather" element={<Weather />} />
          <Route path="/community" element={<Community />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

function RequireAuth() {
  const { initializing, isAuthenticated } = useAuth();

  if (initializing) {
    return <div className="state-banner auth-loading">正在恢复登录状态...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
