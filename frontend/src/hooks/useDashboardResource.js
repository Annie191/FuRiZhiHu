import { useCallback, useEffect, useState } from 'react';

import { getDashboard, getDashboardUsers } from '../api/fucareApi.js';
import { useAuth } from '../context/AuthContext.jsx';

export default function useDashboardResource() {
  const { user: authUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedCity, setSelectedCity] = useState('上海');
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let ignore = false;

    getDashboardUsers()
      .then((data) => {
        if (ignore) return;
        const authOption = authUser
          ? {
              user_id: authUser.id,
              username: authUser.username,
              nickname: authUser.nickname,
              profile_tag: authUser.profile?.profileTag || '',
              latest_date: '',
            }
          : null;
        const mergedUsers =
          authOption && !data.some((item) => item.user_id === authOption.user_id)
            ? [authOption, ...data]
            : data;

        setUsers(mergedUsers);
        if (mergedUsers.length === 0) {
          setError('暂无用户数据');
          setLoading(false);
          return;
        }
        const preferred = authOption || mergedUsers[0];
        setSelectedUserId((current) => current || String(preferred.user_id));
        setSelectedDate((current) => current || preferred.latest_date || '');
      })
      .catch((err) => {
        if (!ignore) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, [authUser]);

  const loadDashboard = useCallback(() => {
    if (!selectedUserId) {
      setLoading(false);
      return undefined;
    }

    setLoading(true);
    setError('');
    return getDashboard(selectedUserId, { date: selectedDate, city: selectedCity })
      .then((data) => {
        setDashboard(data);
        setSelectedDate(data.selected_date);
        if (data.selected_city) setSelectedCity(data.selected_city);
      })
      .catch((err) => {
        setError(err.message);
      })
      .finally(() => setLoading(false));
  }, [selectedCity, selectedDate, selectedUserId]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  return {
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
    reload: loadDashboard,
  };
}
