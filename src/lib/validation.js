import { z } from 'zod';
import { ApiError } from './api-error.js';

const datePattern = /^\d{4}-\d{2}-\d{2}$/;
const dateTimePattern = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/;
const timePattern = /^\d{2}:\d{2}:\d{2}$/;

function validDate(value) {
  return datePattern.test(value) && !Number.isNaN(Date.parse(`${value}T00:00:00Z`));
}

export const date = z.string().refine(validDate, '日期必须为 YYYY-MM-DD。');
export const dateTime = z.string().regex(dateTimePattern, '日期时间必须为 YYYY-MM-DD HH:MM:SS。').refine((value) => !Number.isNaN(Date.parse(value.replace(' ', 'T') + 'Z')), '日期时间无效。');
export const time = z.string().regex(timePattern, '时间必须为 HH:MM:SS。');
export const positiveId = z.coerce.number().int().positive();
export const note = z.string().trim().max(500).nullable().optional();

export function parse(schema, value) {
  const result = schema.safeParse(value);
  if (!result.success) {
    throw new ApiError(400, 'VALIDATION_ERROR', 'Request validation failed.', result.error.issues.map((issue) => ({ path: issue.path.join('.'), message: issue.message })));
  }
  return result.data;
}

export function parseListQuery(query, extra = {}) {
  const schema = z.object({
    page: z.coerce.number().int().min(1).max(10000).default(1),
    pageSize: z.coerce.number().int().min(1).max(100).default(20),
    date: date.optional(),
    from: date.optional(),
    to: date.optional(),
    ...extra,
  }).strict().superRefine((value, ctx) => {
    if (value.date && (value.from || value.to)) ctx.addIssue({ code: 'custom', message: 'date 不能与 from/to 同时使用。', path: ['date'] });
    if ((value.from && !value.to) || (!value.from && value.to)) ctx.addIssue({ code: 'custom', message: 'from 和 to 必须同时提供。', path: ['from'] });
    if (value.from && value.to) {
      const days = (Date.parse(`${value.to}T00:00:00Z`) - Date.parse(`${value.from}T00:00:00Z`)) / 86400000;
      if (days < 0) ctx.addIssue({ code: 'custom', message: 'from 不能晚于 to。', path: ['from'] });
      if (days > 366) ctx.addIssue({ code: 'custom', message: '日期范围不能超过 366 天。', path: ['to'] });
    }
  });
  return parse(schema, query);
}
