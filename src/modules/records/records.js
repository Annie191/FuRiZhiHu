import { Router } from 'express';
import { z } from 'zod';
import { ApiError } from '../../lib/api-error.js';
import { date, dateTime, time, note, parse, parseListQuery, positiveId } from '../../lib/validation.js';

const configs = {
  food: {
    table: 'food_record', dateColumn: 'intake_date', view: 'v_daily_food_summary',
    create: z.object({ foodId: positiveId, mealType: z.enum(['breakfast', 'lunch', 'dinner', 'snack']), amount: z.number().positive().max(10000), amountUnit: z.enum(['g', 'ml']), intakeDate: date, note }).strict(),
    columns: { foodId: 'food_id', mealType: 'meal_type', amount: 'amount', amountUnit: 'amount_unit', intakeDate: 'intake_date', note: 'note' },
  },
  water: {
    table: 'water_record', dateColumn: 'date(intake_time)', view: 'v_daily_water_summary',
    create: z.object({ amountMl: z.number().int().min(50).max(3000), source: z.enum(['water', 'tea', 'soup', 'other']).default('water'), intakeTime: dateTime, note }).strict(),
    columns: { amountMl: 'amount_ml', source: 'source', intakeTime: 'intake_time', note: 'note' },
  },
  sport: {
    table: 'sport_record', dateColumn: 'record_date', view: 'v_daily_sport_summary',
    create: z.object({ sportType: z.string().trim().min(1).max(50), intensity: z.enum(['low', 'medium', 'high']).default('medium'), durationMin: z.number().int().min(1).max(1440), caloriesBurned: z.number().min(0).max(20000).default(0), recordDate: date, startTime: time.nullable().optional(), note }).strict(),
    columns: { sportType: 'sport_type', intensity: 'intensity', durationMin: 'duration_min', caloriesBurned: 'calories_burned', recordDate: 'record_date', startTime: 'start_time', note: 'note' },
  },
  sleep: {
    table: 'sleep_record', dateColumn: 'record_date', view: 'v_daily_sleep_summary',
    create: z.object({ sleepTime: dateTime, wakeTime: dateTime, qualityScore: z.number().int().min(0).max(100), recordDate: date, note }).strict(),
    columns: { sleepTime: 'sleep_time', wakeTime: 'wake_time', qualityScore: 'quality_score', recordDate: 'record_date', note: 'note' },
  },
};

export function createRecordsRouter(db, type) {
  const config = configs[type];
  const router = Router();
  const partial = config.create.partial();

  router.get('/daily-summary', (req, res, next) => {
    try { res.json({ data: summaries(db, type, req.auth.userId, parseListQuery(req.query)) }); } catch (error) { next(error); }
  });
  router.get('/', (req, res, next) => {
    try { res.json({ data: list(db, type, req.auth.userId, parseListQuery(req.query)) }); } catch (error) { next(error); }
  });
  router.post('/', (req, res, next) => {
    try {
      const input = parse(config.create, req.body);
      validateDomain(db, type, input);
      const keys = Object.keys(input);
      const result = db.prepare(`INSERT INTO ${config.table} (user_id, ${keys.map((key) => config.columns[key]).join(', ')}) VALUES (?, ${keys.map(() => '?').join(', ')})`).run(req.auth.userId, ...keys.map((key) => input[key]));
      res.status(201).json({ data: findOwned(db, type, result.lastInsertRowid, req.auth.userId) });
    } catch (error) { next(error); }
  });
  router.get('/:recordId', (req, res, next) => {
    try { res.json({ data: findOwned(db, type, parse(positiveId, req.params.recordId), req.auth.userId) }); } catch (error) { next(error); }
  });
  router.patch('/:recordId', (req, res, next) => {
    try {
      const id = parse(positiveId, req.params.recordId); const input = parse(partial, req.body);
      if (!Object.keys(input).length) throw new ApiError(400, 'VALIDATION_ERROR', 'Request body cannot be empty.');
      const current = findOwned(db, type, id, req.auth.userId);
      const merged = { ...toInput(type, current), ...input };
      validateDomain(db, type, merged);
      const keys = Object.keys(input);
      db.prepare(`UPDATE ${config.table} SET ${keys.map((key) => `${config.columns[key]} = ?`).join(', ')} WHERE record_id = ? AND user_id = ?`).run(...keys.map((key) => input[key]), id, req.auth.userId);
      res.json({ data: findOwned(db, type, id, req.auth.userId) });
    } catch (error) { next(error); }
  });
  router.delete('/:recordId', (req, res, next) => {
    try { const result = db.prepare(`DELETE FROM ${config.table} WHERE record_id = ? AND user_id = ?`).run(parse(positiveId, req.params.recordId), req.auth.userId); if (!result.changes) throw new ApiError(404, 'RESOURCE_NOT_FOUND', 'Record was not found.'); res.status(204).end(); } catch (error) { next(error); }
  });
  return router;
}

function list(db, type, userId, query) {
  const c = configs[type]; const clauses = ['r.user_id = ?']; const values = [userId];
  if (query.date) { clauses.push(`${type === 'water' ? 'date(r.intake_time)' : `r.${c.dateColumn}`} = ?`); values.push(query.date); }
  if (query.from) { clauses.push(`${type === 'water' ? 'date(r.intake_time)' : `r.${c.dateColumn}`} BETWEEN ? AND ?`); values.push(query.from, query.to); }
  const where = clauses.join(' AND ');
  const join = type === 'food' ? ' JOIN food_library f ON f.food_id = r.food_id' : '';
  const total = db.prepare(`SELECT COUNT(*) AS count FROM ${c.table} r${join} WHERE ${where}`).get(...values).count;
  const rows = db.prepare(`SELECT r.*${type === 'food' ? ', f.name AS food_name, f.calorie_kcal, f.protein_g, f.water_ml, f.unit_basis' : ''} FROM ${c.table} r${join} WHERE ${where} ORDER BY ${type === 'water' ? 'r.intake_time' : 'r.record_date'} DESC, r.record_id DESC LIMIT ? OFFSET ?`).all(...values, query.pageSize, (query.page - 1) * query.pageSize);
  return { items: rows.map((row) => map(type, row)), page: query.page, pageSize: query.pageSize, total };
}
function findOwned(db, type, id, userId) {
  const join = type === 'food' ? ' JOIN food_library f ON f.food_id = r.food_id' : '';
  const row = db.prepare(`SELECT r.*${type === 'food' ? ', f.name AS food_name, f.calorie_kcal, f.protein_g, f.water_ml, f.unit_basis' : ''} FROM ${configs[type].table} r${join} WHERE r.record_id = ? AND r.user_id = ?`).get(id, userId);
  if (!row) throw new ApiError(404, 'RESOURCE_NOT_FOUND', 'Record was not found.'); return map(type, row);
}
function summaries(db, type, userId, query) {
  const c = configs[type]; const dateField = type === 'food' ? 'intake_date' : type === 'water' ? 'stat_date' : 'record_date';
  const clauses = ['user_id = ?']; const values = [userId]; if (query.date) { clauses.push(`${dateField} = ?`); values.push(query.date); } if (query.from) { clauses.push(`${dateField} BETWEEN ? AND ?`); values.push(query.from, query.to); }
  const rows = db.prepare(`SELECT * FROM ${c.view} WHERE ${clauses.join(' AND ')} ORDER BY ${dateField}`).all(...values);
  return rows.map((row) => mapSummary(type, row));
}
function validateDomain(db, type, input) {
  if (type === 'sleep') { if (input.wakeTime <= input.sleepTime) throw new ApiError(400, 'VALIDATION_ERROR', 'wakeTime must be later than sleepTime.'); if (input.recordDate !== input.wakeTime.slice(0, 10)) throw new ApiError(400, 'VALIDATION_ERROR', 'recordDate must match wakeTime date.'); }
  if (type === 'food') { const food = db.prepare('SELECT unit_basis FROM food_library WHERE food_id = ?').get(input.foodId); if (!food) throw new ApiError(400, 'VALIDATION_ERROR', 'Food does not exist.'); const expected = food.unit_basis === 'per_100g' ? 'g' : 'ml'; if (input.amountUnit !== expected) throw new ApiError(400, 'VALIDATION_ERROR', `Food amountUnit must be ${expected}.`); }
}
function map(type, r) {
  const base = { id: r.record_id, note: r.note };
  if (type === 'food') return { ...base, foodId:r.food_id, mealType:r.meal_type, amount:r.amount, amountUnit:r.amount_unit, intakeDate:r.intake_date, food:{id:r.food_id,name:r.food_name,calorieKcal:r.calorie_kcal,proteinG:r.protein_g,waterMl:r.water_ml,unitBasis:r.unit_basis} };
  if (type === 'water') return { ...base, amountMl:r.amount_ml, source:r.source, intakeTime:r.intake_time };
  if (type === 'sport') return { ...base, sportType:r.sport_type,intensity:r.intensity,durationMin:r.duration_min,caloriesBurned:r.calories_burned,recordDate:r.record_date,startTime:r.start_time };
  return { ...base, sleepTime:r.sleep_time,wakeTime:r.wake_time,qualityScore:r.quality_score,recordDate:r.record_date };
}
function toInput(type, r) { const { id, ...input } = map(type, r); if (type === 'food') delete input.food; return input; }
function mapSummary(type, r) { if(type==='food')return{date:r.intake_date,totalCalorieKcal:r.total_calorie_kcal,totalProteinG:r.total_protein_g,totalFoodWaterMl:r.total_food_water_ml,foodHealthScore:r.food_health_score}; if(type==='water')return{date:r.stat_date,totalWaterMl:r.total_water_ml,drinkTimes:r.drink_times}; if(type==='sport')return{date:r.record_date,totalDurationMin:r.total_duration_min,totalCaloriesBurned:r.total_calories_burned,sportTimes:r.sport_times}; return{date:r.record_date,sleepHours:r.sleep_hours,sleepQualityScore:r.sleep_quality_score}; }
