import { useEffect, useMemo, useState } from 'react';

import { getDashboardUsers } from '../api/fucareApi.js';
import { useAuth } from '../context/AuthContext.jsx';

export default function useAnalyticsUsers() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState(user ? String(user.id) : '');
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [userError, setUserError] = useState('');

  useEffect(() => {
    let ignore = false;
    setLoadingUsers(true);
    setUserError('');

    getDashboardUsers()
      .then((data) => {
        if (ignore) return;
        const authOption = user
          ? {
              user_id: user.id,
              username: user.username,
              nickname: user.nickname,
              profile_tag: user.profile?.profileTag || '',
              latest_date: '',
            }
          : null;
        const merged =
          authOption && !data.some((item) => item.user_id === authOption.user_id)
            ? [authOption, ...data]
            : data;
        setUsers(merged);
        setSelectedUserId((current) => current || (merged[0] ? String(merged[0].user_id) : ''));
      })
      .catch((error) => {
        if (!ignore) setUserError(error.message);
      })
      .finally(() => {
        if (!ignore) setLoadingUsers(false);
      });

    return () => {
      ignore = true;
    };
  }, [user]);

  const selectedUser = useMemo(
    () => users.find((item) => String(item.user_id) === String(selectedUserId)) || null,
    [selectedUserId, users],
  );

  return {
    users,
    selectedUser,
    selectedUserId,
    setSelectedUserId,
    loadingUsers,
    userError,
  };
}
