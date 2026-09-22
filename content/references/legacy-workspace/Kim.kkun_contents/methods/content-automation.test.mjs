import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, writeFile, rm, readdir } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {
  collectInsights, metricValue, milestone, ageInHours,
  configuration, saveSnapshot, buildReport,
} from './instagram-insights.mjs';
import { registerContent } from './content-intake.mjs';

const config = { token: 'FAKE_TEST_TOKEN', accountId: '123', apiVersion: 'v99.0' };
const now = new Date('2026-09-09T00:00:00Z');
const response = (body, status = 200) => ({ ok: status < 400, status, json: async () => body });
const media = {
  id: '456', caption: '테스트 | 문구\n줄바꿈', media_type: 'VIDEO',
  media_product_type: 'REELS', timestamp: '2026-09-02T00:00:00Z',
};

function fakeApi({ username = 'kim.kkun', failMetric, emptyMetric, pages = false, unsupportedMessage = 'invalid metric' } = {}) {
  let pageCalls = 0;
  return async (url, options) => {
    assert.equal(url.origin, 'https://graph.instagram.com');
    assert.equal(url.searchParams.has('access_token'), false);
    assert.equal(options.headers.Authorization, 'Bearer FAKE_TEST_TOKEN');
    assert.equal(options.redirect, 'error');
    if (url.pathname === '/v99.0/123') return response({ id: '123', username, account_type: 'BUSINESS' });
    if (url.pathname.endsWith('/media')) {
      pageCalls++;
      if (pages && pageCalls === 1) {
        return response({ data: [media], paging: { next: 'https://wrong.example/?access_token=SECRET', cursors: { after: 'opaque' } } });
      }
      if (pages) assert.equal(url.searchParams.get('after'), 'opaque');
      return response({ data: [media] });
    }
    const metric = url.searchParams.get('metric');
    if (failMetric === metric) return response({ error: { code: 190, message: 'FAKE_TEST_TOKEN invalid' } }, 400);
    if (emptyMetric === metric) return response({ data: [] });
    if (metric === 'follows') return response({ error: { code: 100, message: unsupportedMessage } }, 400);
    const value = metric === 'views' ? 1000 : metric === 'shares' ? 0 : 10;
    return response({ data: [{ name: metric, values: [{ value }] }] });
  };
}

test('missing configuration fails before any API request', () => {
  assert.throws(() => configuration({}), /계정 연결 대기/);
});

test('missing metrics are not zeros, and numeric zero is preserved', () => {
  assert.equal(metricValue({ data: [] }, 'views'), null);
  assert.equal(metricValue({ data: [{ name: 'views', values: [{ value: 0 }] }] }, 'views'), 0);
  assert.equal(metricValue({ data: [{ name: 'views', total_value: { value: 12 } }] }, 'views'), 12);
  assert.equal(metricValue({ data: [{ name: 'views', values: [{ value: 'unknown' }] }] }, 'views'), null);
});

test('measurement windows do not pass off old data as day 7', () => {
  assert.equal(milestone(167.999), 'other');
  assert.equal(milestone(168), 'day7');
  assert.equal(milestone(191.999), 'day7');
  assert.equal(milestone(192), 'other');
  assert.equal(milestone(ageInHours('2026-09-02T00:00:00.001Z', now.toISOString())), 'other');
  assert.throws(() => ageInHours('2027-01-01', now.toISOString()), /게시일/);
});

test('pagination is owned-host only, duplicate media are merged, unsupported data remains null', async () => {
  const snapshot = await collectInsights({ ...config, now, fetchImpl: fakeApi({ pages: true, emptyMetric: 'reach' }) });
  assert.equal(snapshot.media.length, 1);
  assert.equal(snapshot.media[0].milestone, 'day7');
  assert.equal(snapshot.media[0].metrics.shares.value, 0);
  assert.equal(snapshot.media[0].metrics.follows.status, 'unsupported');
  assert.equal(snapshot.media[0].metrics.reach.status, 'unavailable');
  assert.equal(JSON.stringify(snapshot).includes(config.token), false);
  const report = buildReport([snapshot]);
  assert.match(report, /7일차 비교 가능 자료/);
  assert.match(report, /테스트   문구 줄바꿈/);
});

test('wrong account and expired tokens fail without exposing credentials', async () => {
  await assert.rejects(collectInsights({ ...config, now, fetchImpl: fakeApi({ username: 'someone_else' }) }), /일치하지 않아/);
  await assert.rejects(collectInsights({ ...config, now, fetchImpl: fakeApi({ failMetric: 'views' }) }), error => {
    assert.match(error.message, /code 190/);
    assert.equal(error.message.includes(config.token), false);
    return true;
  });
});

test('rate limits have bounded retries', async () => {
  let calls = 0;
  await assert.rejects(collectInsights({
    ...config, now, wait: async () => {},
    fetchImpl: async () => { calls++; return response({ error: { code: 4 } }, 429); },
  }), /HTTP 429/);
  assert.equal(calls, 3);
});

test('snapshot retry cannot overwrite an existing raw observation', async t => {
  const directory = await mkdtemp(path.join(os.tmpdir(), 'kimkkun-insights-test-'));
  t.after(() => rm(directory, { recursive: true, force: true }));
  const snapshot = await collectInsights({ ...config, now, fetchImpl: fakeApi() });
  const saved = await saveSnapshot(snapshot, directory);
  const original = await readFile(saved, 'utf8');
  await assert.rejects(saveSnapshot({ ...snapshot, media: [] }, directory), { code: 'EEXIST' });
  assert.equal(await readFile(saved, 'utf8'), original);
  assert.equal((await readdir(directory)).length, 1);
});

test('registering identical video and script is idempotent; script revisions remain distinct', async t => {
  const directory = await mkdtemp(path.join(os.tmpdir(), 'kimkkun-intake-test-'));
  t.after(() => rm(directory, { recursive: true, force: true }));
  const videoPath = path.join(directory, 'source.mov');
  const scriptPath = path.join(directory, 'script.md');
  // Fixture bytes validate bookkeeping only; they are not a playable video.
  await writeFile(videoPath, 'TEST VIDEO BYTES');
  await writeFile(scriptPath, '수환 대본 첫 버전');
  const input = { videoPath, scriptPath, outputDir: directory, now };
  const first = await registerContent(input);
  const repeated = await registerContent(input);
  assert.equal(first.created, true);
  assert.equal(repeated.created, false);
  assert.equal(first.path, repeated.path);
  const manifest = JSON.parse(await readFile(first.path, 'utf8'));
  assert.equal(manifest.status, 'registered_only');
  assert.equal(manifest.script_snapshot.text, '수환 대본 첫 버전');
  assert.equal(manifest.instagram.media_id, null);
  assert.equal(manifest.editor.application, 'Palmier Pro');
  assert.equal(manifest.editor.project_path, null);
  await writeFile(scriptPath, '수환 대본 두 번째 버전');
  const revised = await registerContent(input);
  assert.notEqual(first.content_id, revised.content_id);
  assert.equal(await readFile(videoPath, 'utf8'), 'TEST VIDEO BYTES');
  assert.equal(JSON.parse(await readFile(first.path, 'utf8')).script_snapshot.text, '수환 대본 첫 버전');
});

test('actual Instagram unsupported follows response does not discard other metrics', async () => {
  const snapshot = await collectInsights({ ...config, now, fetchImpl: fakeApi({
    unsupportedMessage: 'The Media Insights API does not support the follows metric for this media product type.',
  }) });
  assert.equal(snapshot.media[0].metrics.follows.status, 'unsupported');
  assert.equal(snapshot.media[0].metrics.follows.value, null);
  assert.equal(snapshot.media[0].metrics.views.value, 1000);
});

test('hourly discovery collects new posts and actual milestone crossings within the same day', async () => {
  const { dueMedia } = await import('./instagram-insights.mjs');
  const items = [{ id: '1', timestamp: '2026-09-20T12:00:00Z' }, { id: '2', timestamp: '2026-09-21T12:30:00Z' }];
  const previous = [{ collected_at: '2026-09-21T11:00:00Z', media: [{ ...items[0], milestone: 'other' }] }];
  assert.deepEqual(dueMedia(items, previous, new Date('2026-09-21T13:00:00Z')).map(x => x.id), ['1', '2']);
  const observed = [{ collected_at: '2026-09-21T13:00:00Z', media: items.map((item, i) => ({ ...item, milestone: i === 0 ? 'day1' : 'other' })) }];
  assert.equal(dueMedia(items, observed, new Date('2026-09-21T14:00:00Z')).length, 0);
  assert.equal(dueMedia(items, observed, new Date('2026-09-22T01:00:00Z')).length, 2);
});

test('discovery keeps the latest ten, follows only owned-host cursors, and strips old posts', async () => {
  const { discoverMedia } = await import('./instagram-insights.mjs');
  let calls = 0;
  const result = await discoverMedia({ token: 'private-token', accountId: '123', apiVersion: 'v26.0', now: new Date('2026-09-22T00:00:00Z'), fetchImpl: async (url, options) => {
    assert.equal(url.hostname, 'graph.instagram.com');
    assert.equal(url.searchParams.has('access_token'), false);
    assert.equal(options.headers.Authorization, 'Bearer private-token');
    calls++;
    return { ok: true, json: async () => calls === 1 ? { data: Array.from({length: 10}, (_, i) => ({ id: String(i + 1), timestamp: '2026-08-01T00:00:00Z' })), paging: { next: 'https://evil.example/?access_token=secret', cursors: { after: 'next' } } } : { data: [{ id: '11', timestamp: '2026-07-01T00:00:00Z' }] } };
  } });
  assert.equal(calls, 2);
  assert.equal(result.length, 10);
  assert.equal(result.some(x => x.id === '11'), false);
});
