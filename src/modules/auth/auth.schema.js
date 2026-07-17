import { z } from 'zod';
import { ApiError } from '../../lib/api-error.js';

const optionalPhone = z
  .string()
  .trim()
  .regex(/^1[3-9]\d{9}$/, '手机号格式不正确。')
  .optional();

const optionalEmail = z.string().trim().email('邮箱格式不正确。').transform((value) => value.toLowerCase()).optional();

const profileSchema = z
  .object({
    age: z.number().int().min(10).max(100),
    gender: z.enum(['male', 'female', 'other']),
    heightCm: z.number().finite().min(100).max(250),
    weightKg: z.number().finite().min(20).max(300),
    goal: z.enum(['lose_fat', 'maintain', 'gain_muscle']),
    activityLevel: z.enum(['low', 'medium', 'high']),
    avgSleepHours: z.number().finite().min(0).max(24),
    waterTargetMl: z.number().int().min(500).max(6000).default(2200),
    profileTag: z.string().trim().min(1).max(100),
  })
  .strict();

const registerSchema = z
  .object({
    username: z.string().trim().regex(/^[A-Za-z0-9_-]{3,32}$/, '用户名需为 3-32 位字母、数字、下划线或连字符。'),
    password: z.string().min(12).max(128),
    nickname: z.string().trim().min(1).max(50),
    phone: optionalPhone,
    email: optionalEmail,
    profile: profileSchema,
  })
  .strict();

const loginSchema = z
  .object({
    identifier: z.string().trim().min(1).max(254),
    password: z.string().min(1).max(128),
  })
  .strict();

export function parseRegistration(body) {
  return parse(registerSchema, body);
}

export function parseLogin(body) {
  return parse(loginSchema, body);
}

function parse(schema, body) {
  const result = schema.safeParse(body);

  if (!result.success) {
    throw new ApiError(
      400,
      'VALIDATION_ERROR',
      'Request validation failed.',
      result.error.issues.map((issue) => ({ path: issue.path.join('.'), message: issue.message })),
    );
  }

  return result.data;
}
