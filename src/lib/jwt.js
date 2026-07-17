import jwt from 'jsonwebtoken';

const algorithm = 'HS256';

export function signToken({ userId, username }, config) {
  return jwt.sign(
    { username },
    config.jwtSecret,
    { algorithm, subject: String(userId), expiresIn: config.jwtExpiresIn },
  );
}

export function verifyToken(token, config) {
  const payload = jwt.verify(token, config.jwtSecret, { algorithms: [algorithm] });

  if (!Number.isSafeInteger(Number(payload.sub)) || typeof payload.username !== 'string') {
    throw new Error('Invalid token payload.');
  }

  return {
    userId: Number(payload.sub),
    username: payload.username,
  };
}
