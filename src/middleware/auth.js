import { ApiError } from '../lib/api-error.js';
import { verifyToken } from '../lib/jwt.js';

export function requireAuth({ config, authService }) {
  return (req, _res, next) => {
    const authorization = req.get('authorization');

    if (!authorization?.startsWith('Bearer ') || authorization.length === 'Bearer '.length) {
      return next(new ApiError(401, 'AUTH_REQUIRED', 'Authentication token is required.'));
    }

    try {
      const tokenAuth = verifyToken(authorization.slice('Bearer '.length), config);
      const principal = authService.getActivePrincipal(tokenAuth.userId);

      if (!principal || principal.username !== tokenAuth.username) {
        throw new Error('Inactive account.');
      }

      req.auth = Object.freeze(tokenAuth);
      return next();
    } catch {
      return next(new ApiError(401, 'INVALID_TOKEN', 'Authentication token is invalid or expired.'));
    }
  };
}
