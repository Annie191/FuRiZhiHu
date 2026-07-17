const publicUserProjection = `
  SELECT
    ua.user_id,
    ua.username,
    ua.nickname,
    ua.phone,
    ua.email,
    ua.status,
    up.age,
    up.gender,
    up.height_cm,
    up.weight_kg,
    up.goal,
    up.activity_level,
    up.avg_sleep_hours,
    up.water_target_ml,
    up.profile_tag,
    up.bmi
  FROM user_account ua
  INNER JOIN user_profile up ON up.user_id = ua.user_id
`;

export function createAuthRepository(db) {
  const findCredential = db.prepare(`
    SELECT user_id, username, password_hash, status
    FROM user_account
    WHERE username = ? OR phone = ? OR email = ?
    LIMIT 1
  `);
  const findPublicById = db.prepare(`${publicUserProjection} WHERE ua.user_id = ?`);
  const findActiveById = db.prepare('SELECT user_id, username FROM user_account WHERE user_id = ? AND status = 1');
  const insertAccount = db.prepare(`
    INSERT INTO user_account (username, password_hash, nickname, phone, email)
    VALUES (?, ?, ?, ?, ?)
  `);
  const insertProfile = db.prepare(`
    INSERT INTO user_profile (
      user_id, age, gender, height_cm, weight_kg, goal,
      activity_level, avg_sleep_hours, water_target_ml, profile_tag
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  return {
    findCredential(identifier) {
      return findCredential.get(identifier, identifier, identifier);
    },
    findPublicById(userId) {
      return findPublicById.get(userId);
    },
    findActiveById(userId) {
      return findActiveById.get(userId);
    },
    createUser(input, passwordHash) {
      return db.transaction(() => {
        const account = insertAccount.run(input.username, passwordHash, input.nickname, input.phone ?? null, input.email ?? null);
        const profile = input.profile;
        insertProfile.run(
          account.lastInsertRowid,
          profile.age,
          profile.gender,
          profile.heightCm,
          profile.weightKg,
          profile.goal,
          profile.activityLevel,
          profile.avgSleepHours,
          profile.waterTargetMl,
          profile.profileTag,
        );
        return findPublicById.get(account.lastInsertRowid);
      })();
    },
  };
}
