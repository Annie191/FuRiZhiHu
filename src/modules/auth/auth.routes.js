import { Router } from 'express';
import { requireAuth } from '../../middleware/auth.js';
import { parseLogin, parseRegistration } from './auth.schema.js';

export function createAuthRouter({ authService, config }) {
  const router = Router();

  router.post('/register', (req, res, next) => {
    try {
      const payload = authService.register(parseRegistration(req.body));
      res.status(201).json({ data: payload });
    } catch (error) {
      next(error);
    }
  });

  router.post('/login', (req, res, next) => {
    try {
      const payload = authService.login(parseLogin(req.body));
      res.json({ data: payload });
    } catch (error) {
      next(error);
    }
  });

  router.get('/me', requireAuth({ config, authService }), (req, res) => {
    res.json({ data: { user: authService.getCurrentUser(req.auth.userId) } });
  });

  return router;
}
