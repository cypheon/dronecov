import fetch from 'node-fetch';
import fs from 'fs';
import lcovParse from 'lcov-parse';
import process from 'process';

const log = console;

function getPercentage(cov, key) {
  const hit = cov.map(x => x[key]).reduce((acc, entry) => acc + entry.hit, 0);
  const found = cov.map(x => x[key]).reduce((acc, entry) => acc + entry.found, 0);
  return hit / found;
}

function parsePromise(filename) {
  return new Promise((resolve, reject) => {
    lcovParse(filename, (error, result) => {
      if (error !== null) {
        reject(error);
      }
      resolve(result);
    });
  });
}

function main(config) {
  const target = new URL(`${config.repo}/${config.branch}/coverage`, config.server);

  log.info(`reading LCOV info from ${config.info_filename}`);

  return parsePromise(config.info_filename).then(data => {
    const summary = {
      lines: getPercentage(data, "lines"),
      functions: getPercentage(data, "functions"),
    };
    log.info("info file parsed", {summary});

    log.info(`upload summary to ${target}`);
    return fetch(target, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${config.token}`,
      },
      body: JSON.stringify({
        coverage_total: 100 * summary.lines,
        build_number: config.build_number,
      }),
    }).then((response) => {
      if (response.ok && response.status === 201) {
        log.info('upload complete');
      } else {
        log.error(
          'upload failed',
          {response,
            resBody: response.body}
        );
        throw new Error(`upload failed: ${response.status} ${response.statusText}`);
      }
    });
  });
}

main({
  server: process.env.PLUGIN_SERVER,
  repo: process.env.DRONE_REPO,
  branch: process.env.DRONE_COMMIT_BRANCH,
  token: process.env.DRONECOV_ACCESS_TOKEN,
  build_number: process.env.DRONE_BUILD_NUMBER,
  info_filename: process.env.PLUGIN_LCOV_INFO,
}).catch((error) => {
  log.error('Failed to upload coverage info', {error});
  process.exit(1);
});
