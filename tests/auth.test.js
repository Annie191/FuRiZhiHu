import bcrypt from 'bcryptjs';
import request from 'supertest';
import { beforeEach, describe, expect, it } from 'vitest';
import { createApp } from '../src/app.js';
import { createTestDatabase, testConfig } from './setup.js';

const registration = {
  username: 'health_user',
  password: 'a-secure-password',
  nickname: '健康同学',
  phone: '13800138003',
  email: 'health@example.com',
  profile: {
    age: 24,
    gender: 'female',
    heightCm: 165,
    weightKg: 55,
    goal: 'maintain',
    activityLevel: 'medium',
    avgSleepHours: 7.5,
    waterTargetMl: 2100,
    profileTag: '稳定作息型用户',
  },
};

describe('authentication API', () => {
  let db;
  let app;

  beforeEach(() => {
    db = createTestDatabase();
    app = createApp({ config: testConfig, db });
  });

  it('registers a complete account and returns a sanitized access token payload', async () => {
    const response = await request(app).post('/api/v1/auth/register').send(registration);

    expect(response.status).toBe(201);
    expect(response.body.data.tokenType).toBe('Bearer');
    expect(response.body.data.accessToken).toEqual(expect.any(String));
    expect(response.body.data.user).toMatchObject({
      username: registration.username,
      nickname: registration.nickname,
      profile: { bmi: 20.2, profileTag: registration.profile.profileTag },
    });
    expect(response.body.data.user).not.toHaveProperty('password_hash');

    const storedAccount = db.prepare('SELECT password_hash FROM user_account WHERE username = ?').get(registration.username);
    expect(storedAccount.password_hash).not.toBe(registration.password);
    expect(bcrypt.compareSync(registration.password, storedAccount.password_hash)).toBe(true);
    expect(db.prepare('SELECT COUNT(*) AS count FROM user_profile').get().count).toBe(1);
  });

  it('rejects duplicate identifiers without creating a partial account', async () => {
    await request(app).post('/api/v1/auth/register').send(registration).expect(201);
    const response = await request(app).post('/api/v1/auth/register').send({
      ...registration,
      username: 'another_user',
    });

    expect(response.status).toBe(409);
    expect(response.body.error.code).toBe('ACCOUNT_IDENTIFIER_TAKEN');
    expect(db.prepare('SELECT COUNT(*) AS count FROM user_account').get().count).toBe(1);
    expect(db.prepare('SELECT COUNT(*) AS count FROM user_profile').get().count).toBe(1);
  });

  it('rejects invalid profile data before persistence', async () => {
    const response = await request(app).post('/api/v1/auth/register').send({
      ...registration,
      profile: { ...registration.profile, age: 9 },
    });

    expect(response.status).toBe(400);
    expect(response.body.error.code).toBe('VALIDATION_ERROR');
    expect(db.prepare('SELECT COUNT(*) AS count FROM user_account').get().count).toBe(0);
  });

  it('logs in by username, phone, and email', async () => {
    await request(app).post('/api/v1/auth/register').send(registration).expect(201);

    for (const identifier of [registration.username, registration.phone, registration.email]) {
      const response = await request(app).post('/api/v1/auth/login').send({
        identifier,
        password: registration.password,
      });

      expect(response.status).toBe(200);
      expect(response.body.data.user.username).toBe(registration.username);
      expect(response.body.data.accessToken).toEqual(expect.any(String));
    }
  });

  it('uses one credential error for wrong passwords and disabled accounts', async () => {
    await request(app).post('/api/v1/auth/register').send(registration).expect(201);
    const wrongPassword = await request(app).post('/api/v1/auth/login').send({
      identifier: registration.username,
      password: 'incorrect-password',
    });
    db.prepare('UPDATE user_account SET status = 0 WHERE username = ?').run(registration.username);
    const disabledAccount = await request(app).post('/api/v1/auth/login').send({
      identifier: registration.username,
      password: registration.password,
    });

    expect(wrongPassword.status).toBe(401);
    expect(disabledAccount.status).toBe(401);
    expect(wrongPassword.body).toEqual(disabledAccount.body);
    expect(wrongPassword.body.error.code).toBe('INVALID_CREDENTIALS');
  });

  it('returns the current user only for an active valid token', async () => {
    const registrationResponse = await request(app).post('/api/v1/auth/register').send(registration);
    const token = registrationResponse.body.data.accessToken;

    const response = await request(app)
      .get('/api/v1/auth/me')
      .set('Authorization', `Bearer ${token}`);

    expect(response.status).toBe(200);
    expect(response.body.data.user.username).toBe(registration.username);
    expect(response.body.data.user).not.toHaveProperty('password_hash');
  });

  it('rejects missing, tampered, and disabled-token authentication', async () => {
    const registrationResponse = await request(app).post('/api/v1/auth/register').send(registration);
    const token = registrationResponse.body.data.accessToken;

    const missingToken = await request(app).get('/api/v1/auth/me');
    const tamperedToken = await request(app)
      .get('/api/v1/auth/me')
      .set('Authorization', `Bearer ${token}tampered`);
    db.prepare('UPDATE user_account SET status = 0 WHERE username = ?').run(registration.username);
    const disabledToken = await request(app)
      .get('/api/v1/auth/me')
      .set('Authorization', `Bearer ${token}`);

    expect(missingToken.status).toBe(401);
    expect(missingToken.body.error.code).toBe('AUTH_REQUIRED');
    expect(tamperedToken.status).toBe(401);
    expect(tamperedToken.body.error.code).toBe('INVALID_TOKEN');
    expect(disabledToken.status).toBe(401);
    expect(disabledToken.body.error.code).toBe('INVALID_TOKEN');
  });
});
