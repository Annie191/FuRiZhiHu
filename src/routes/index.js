import { Router } from 'express';
import { createFoodsRouter } from '../modules/foods/foods.routes.js';
import { createProfileRouter } from '../modules/profile/profile.routes.js';
import { createProfileService } from '../modules/profile/profile.service.js';
import { createRecordsRouter } from '../modules/records/records.js';
import { requireAuth } from '../middleware/auth.js';
import { createAuthRepository } from '../modules/auth/auth.repository.js';
import { createAuthRouter } from '../modules/auth/auth.routes.js';
import { createAuthService } from '../modules/auth/auth.service.js';
import { createHealthRouter } from './health.routes.js';

export function createApiRouter({ config, db }) {
  const router = Router();
  const authService = createAuthService({ config, repository: createAuthRepository(db) });
  const authenticated = requireAuth({ config, authService });

  router.use(createHealthRouter(db));
  router.use('/auth', createAuthRouter({ authService, config }));
  router.use('/foods', createFoodsRouter(db));
  router.use('/profile', authenticated, createProfileRouter(createProfileService(db)));
  router.use('/food-records', authenticated, createRecordsRouter(db, 'food'));
  router.use('/water-records', authenticated, createRecordsRouter(db, 'water'));
  router.use('/sport-records', authenticated, createRecordsRouter(db, 'sport'));
  router.use('/sleep-records', authenticated, createRecordsRouter(db, 'sleep'));

  return router;
}
