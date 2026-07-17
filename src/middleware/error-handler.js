import { ApiError } from '../lib/api-error.js';

function sqliteError(error) {
  if (!error.code?.startsWith('SQLITE_CONSTRAINT')) {
    return null;
  }

  if (error.code.includes('UNIQUE') || error.code.includes('PRIMARYKEY')) {
    return new ApiError(409, 'CONFLICT', 'The submitted data conflicts with an existing record.');
  }

  return new ApiError(400, 'VALIDATION_ERROR', 'The submitted data violates a database constraint.');
}

export function errorHandler(error, _req, res, _next) {
  const normalizedError =
    error instanceof ApiError
      ? error
      : error instanceof SyntaxError && 'body' in error
        ? new ApiError(400, 'VALIDATION_ERROR', 'Request body must be valid JSON.')
        : sqliteError(error) ?? new ApiError(500, 'INTERNAL_ERROR', 'An unexpected error occurred.');

  const response = {
    error: {
      code: normalizedError.code,
      message: normalizedError.message,
      details: normalizedError.details,
    },
  };

  res.status(normalizedError.status).json(response);
}
