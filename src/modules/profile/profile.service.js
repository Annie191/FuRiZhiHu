import { ApiError } from '../../lib/api-error.js';

const columns = { age: 'age', gender: 'gender', heightCm: 'height_cm', weightKg: 'weight_kg', goal: 'goal', activityLevel: 'activity_level', avgSleepHours: 'avg_sleep_hours', waterTargetMl: 'water_target_ml', profileTag: 'profile_tag' };
const projection = 'age, gender, height_cm, weight_kg, goal, activity_level, avg_sleep_hours, water_target_ml, profile_tag, bmi';

export function createProfileService(db) {
  const get = db.prepare(`SELECT ${projection} FROM user_profile WHERE user_id = ?`);
  return {
    get(userId) { const row = get.get(userId); if (!row) throw new ApiError(404, 'RESOURCE_NOT_FOUND', 'Health profile was not found.'); return map(row); },
    update(userId, input) {
      const entries = Object.entries(input);
      const sql = `UPDATE user_profile SET ${entries.map(([key]) => `${columns[key]} = ?`).join(', ')} WHERE user_id = ?`;
      db.prepare(sql).run(...entries.map(([, value]) => value), userId);
      return this.get(userId);
    },
  };
}
function map(row) { return { age: row.age, gender: row.gender, heightCm: row.height_cm, weightKg: row.weight_kg, bmi: row.bmi, goal: row.goal, activityLevel: row.activity_level, avgSleepHours: row.avg_sleep_hours, waterTargetMl: row.water_target_ml, profileTag: row.profile_tag }; }
