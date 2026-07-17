import { ApiError } from '../lib/api-error.js';

export function notFound(req, _res, next) {
  next(new ApiError(404, 'RESOURCE_NOT_FOUND', `Route ${req.method} ${req.originalUrl} was not found.`));
}
