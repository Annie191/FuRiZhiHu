import cors from 'cors';
import express from 'express';
import helmet from 'helmet';
import { errorHandler } from './middleware/error-handler.js';
import { notFound } from './middleware/not-found.js';
import { createApiRouter } from './routes/index.js';

export function createApp({ config, db }) {
  const app = express();

  app.disable('x-powered-by');
  app.use(helmet());
  app.use(cors({ origin: config.corsOrigin }));
  app.use(express.json({ limit: '1mb' }));

  if (config.nodeEnv === 'development') {
    app.use((req, _res, next) => {
      console.info(`${req.method} ${req.originalUrl}`);
      next();
    });
  }

  app.use('/api/v1', createApiRouter({ config, db }));
  app.use(notFound);
  app.use(errorHandler);

  return app;
}
