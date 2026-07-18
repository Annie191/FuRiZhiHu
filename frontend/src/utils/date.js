export function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

export function addDays(dateText, offset) {
  const date = new Date(`${dateText}T00:00:00`);
  date.setDate(date.getDate() + offset);
  return date.toISOString().slice(0, 10);
}

export function recentRange(days = 7, endDate = todayIso()) {
  return {
    from: addDays(endDate, -(days - 1)),
    to: endDate,
  };
}

export function expandDates(start, count) {
  return Array.from({ length: count }, (_, index) => addDays(start, index));
}

export function shortDate(dateText) {
  return dateText ? dateText.slice(5) : '';
}
