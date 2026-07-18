export default function UserSelect({ users, value, onChange, disabled = false }) {
  return (
    <label>
      <span>用户</span>
      <select value={value} onChange={(event) => onChange(event.target.value)} disabled={disabled}>
        {users.map((user) => (
          <option key={user.user_id} value={user.user_id}>
            {user.nickname || user.username}
          </option>
        ))}
      </select>
    </label>
  );
}
