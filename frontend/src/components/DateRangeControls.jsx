export default function DateRangeControls({ from, to, onFromChange, onToChange }) {
  return (
    <>
      <label>
        <span>开始</span>
        <input type="date" value={from} onChange={(event) => onFromChange(event.target.value)} />
      </label>
      <label>
        <span>结束</span>
        <input type="date" value={to} onChange={(event) => onToChange(event.target.value)} />
      </label>
    </>
  );
}
