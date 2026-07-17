import bcrypt from 'bcryptjs';
import { ApiError } from '../../lib/api-error.js';
import { signToken } from '../../lib/jwt.js';

const passwordRounds = 12;
const timingSafeHash = '$2b$12$FBCJFKLkwjQw3lBcPTsO7u4KhVyrpXzoWx8ck2fCeumBGSj/CfT6q';

export function createAuthService({ config, repository }) {
  return {
    register(input) {
      const passwordHash = bcrypt.hashSync(input.password, passwordRounds);

      try {
        const user = repository.createUser(input, passwordHash);
        return buildAuthPayload(user, config);
      } catch (error) {
        if (error.code?.startsWith('SQLITE_CONSTRAINT')) {
          throw new ApiError(409, 'ACCOUNT_IDENTIFIER_TAKEN', 'An account with those identifiers already exists.');
        }
        throw error;
      }
    },
    login(input) {
      const account = repository.findCredential(input.identifier);
      const passwordHash = account?.password_hash ?? timingSafeHash;
      const passwordMatches = bcrypt.compareSync(input.password, passwordHash);

      if (!account || !passwordMatches || account.status !== 1) {
        throw new ApiError(401, 'INVALID_CREDENTIALS', 'Invalid credentials.');
      }

      const user = repository.findPublicById(account.user_id);
      return buildAuthPayload(user, config);
    },
    getCurrentUser(userId) {
      const user = repository.findPublicById(userId);

      if (!user || user.status !== 1) {
        throw new ApiError(401, 'INVALID_TOKEN', 'Authentication token is invalid.');
      }

      return formatUser(user);
    },
    getActivePrincipal(userId) {
      return repository.findActiveById(userId);
    },
  };
}

function buildAuthPayload(user, config) {
  return {
    accessToken: signToken({ userId: user.user_id, username: user.username }, config),
    tokenType: 'Bearer',
    user: formatUser(user),
  };
}

export function formatUser(user) {
  return {
    id: user.user_id,
    username: user.username,
    nickname: user.nickname,
    phone: user.phone,
    email: user.email,
    profile: {
      age: user.age,
      gender: user.gender,
      heightCm: user.height_cm,
      weightKg: user.weight_kg,
      goal: user.goal,
      activityLevel: user.activity_level,
      avgSleepHours: user.avg_sleep_hours,
      waterTargetMl: user.water_target_ml,
      profileTag: user.profile_tag,
      bmi: user.bmi,
    },
  };
}
