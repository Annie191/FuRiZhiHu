import { ApiError } from '../../lib/api-error.js';
import { parse } from '../../lib/validation.js';
import { z } from 'zod';

const editable = z.object({
  age: z.number().int().min(10).max(100).optional(), gender: z.enum(['male', 'female', 'other']).optional(),
  heightCm: z.number().finite().min(100).max(250).optional(), weightKg: z.number().finite().min(20).max(300).optional(),
  goal: z.enum(['lose_fat', 'maintain', 'gain_muscle']).optional(), activityLevel: z.enum(['low', 'medium', 'high']).optional(),
  avgSleepHours: z.number().finite().min(0).max(24).optional(), waterTargetMl: z.number().int().min(500).max(6000).optional(),
  profileTag: z.string().trim().min(1).max(100).optional(),
}).strict();

export function parseProfilePatch(body) {
  const value = parse(editable, body);
  if (Object.keys(value).length === 0) throw new ApiError(400, 'VALIDATION_ERROR', 'Request body cannot be empty.');
  return value;
}
