import { createApp } from './app.js';
import { loadConfig } from './config/env.js';
import { openDatabase } from './db/sqlite.js';

const config = loadConfig();
const db = openDatabase(config);
const app = createApp({ config, db });
const server = app.listen(config.port, config.host, () => {
  console.info(`FuCare API listening on http://${config.host}:${config.port}`);
});

function shutdown(signal) {
  console.info(`Received ${signal}, shutting down.`);
  server.close(() => {
    db.close();
    process.exit(0);
  });
}

process.once('SIGINT', () => shutdown('SIGINT'));
process.once('SIGTERM', () => shutdown('SIGTERM'));
