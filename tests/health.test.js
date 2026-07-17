import request from 'supertest';
import { beforeEach, describe, expect, it } from 'vitest';
import { createApp } from '../src/app.js';
import { createTestDatabase, testConfig } from './setup.js';

describe('GET /api/v1/health', () => {
  let db;
  let app;

  beforeEach(() => {
    db = createTestDatabase();
    app = createApp({ config: testConfig, db });
  });

  it('reports API and database readiness', async () => {
    const response = await request(app).get('/api/v1/health');

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      status: 'ok',
      service: 'fucare-api',
      database: 'ok',
    });
  });

  it('returns a safe 503 response when the database cannot be queried', async () => {
    db.close();

    const response = await request(app).get('/api/v1/health');

    expect(response.status).toBe(503);
    expect(response.body).toEqual({
      error: {
        code: 'SERVICE_UNAVAILABLE',
        message: 'Database is unavailable.',
        details: null,
      },
    });
  });
});

describe('unmatched routes', () => {
  it('returns the shared error envelope', async () => {
    const app = createApp({ config: testConfig, db: createTestDatabase() });
    const response = await request(app).get('/api/v1/missing');

    expect(response.status).toBe(404);
    expect(response.body.error.code).toBe('RESOURCE_NOT_FOUND');
    expect(response.body.error.details).toBeNull();
  });
});
