import { Router } from 'express';
import { ApiError } from '../lib/api-error.js';

export function createHealthRouter(db) {
  const router = Router();

  router.get('/health', (_req, res, next) => {
    try {
      db.prepare('SELECT 1 AS ready').get();
      res.json({
        status: 'ok',
        service: 'fucare-api',
        database: 'ok',
      });
    } catch {
      next(new ApiError(503, 'SERVICE_UNAVAILABLE', 'Database is unavailable.'));
    }
  });

  return router;
}
