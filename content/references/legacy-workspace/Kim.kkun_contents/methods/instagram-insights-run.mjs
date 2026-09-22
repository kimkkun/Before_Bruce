#!/usr/bin/env node
// Local scheduled runner. Credentials stay outside the repository.
import { readFile, writeFile, rename, stat } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { collectInsights, saveSnapshot, regenerateReport, discoverMedia, dueMedia, readSnapshots } from './instagram-insights.mjs';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const directory = path.join(os.homedir(), '.config/kimkkun-insights');
const credentialPath = path.join(directory, 'credentials.json');
const statusPath = path.join(directory, 'status.json');
const now = new Date();
async function atomicJson(file, value) {
  const temporary = file + '.' + process.pid + '.tmp';
  await writeFile(temporary, JSON.stringify(value, null, 2) + '\n', { mode: 0o600, flag: 'wx' });
  await rename(temporary, file);
}
function notify() {
  try {
    execFileSync('/usr/bin/osascript', ['-e', 'display notification "Instagram 성과 수집 상태를 확인해줘. 자동화 상태 파일에 오류를 기록했어." with title "김꾼 인사이트"'], { stdio: 'ignore', timeout: 10000 });
  } catch { /* status.json is the durable failure record */ }
}
let credentials;
try {
  credentials = JSON.parse(await readFile(credentialPath, 'utf8'));
  if (!credentials.issued_at) {
    credentials.issued_at = (await stat(credentialPath)).mtime.toISOString();
    await atomicJson(credentialPath, credentials);
  }
  let refreshWarning;
  // Refresh weekly, safely beyond the minimum 24-hour age for long-lived tokens.
  const tokenAge = now - new Date(credentials.refreshed_at ?? credentials.issued_at);
  if (tokenAge >= 7 * 86400000) {
    try {
      const response = await fetch('https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token', {
        headers: { Authorization: 'Bearer ' + credentials.access_token },
        redirect: 'error', signal: AbortSignal.timeout(30000),
      });
      const body = await response.json();
      if (!response.ok || body.error || !/^IG[A-Za-z0-9_-]{30,}$/.test(body.access_token ?? '') || !(body.expires_in > 0)) {
        throw new Error('토큰 갱신 실패: HTTP ' + response.status + ', code ' + (body.error?.code ?? 'unknown'));
      }
      // Verify identity before replacing working credentials.
      const check = await fetch('https://graph.instagram.com/' + credentials.api_version + '/me?fields=id,username', {
        headers: { Authorization: 'Bearer ' + body.access_token }, redirect: 'error', signal: AbortSignal.timeout(30000),
      });
      const account = await check.json();
      if (!check.ok || account.username !== 'kim.kkun' || account.id !== credentials.account_id) throw new Error('갱신 토큰 계정 검증 실패');
      credentials = { ...credentials, access_token: body.access_token, refreshed_at: now.toISOString(), expires_at: new Date(now.getTime() + body.expires_in * 1000).toISOString() };
      await atomicJson(credentialPath, credentials);
    } catch { refreshWarning = '토큰 자동 갱신 실패. 기존 토큰으로 수집하며 재인증 여부를 확인해야 함.'; }
  }
  const verification = await fetch('https://graph.instagram.com/' + credentials.api_version + '/me?fields=id,username', {
    headers: { Authorization: 'Bearer ' + credentials.access_token }, redirect: 'error', signal: AbortSignal.timeout(30000),
  });
  const identity = await verification.json();
  if (!verification.ok || identity.username !== 'kim.kkun' || identity.id !== credentials.account_id) {
    throw new Error('Instagram 연결 검증 실패: HTTP ' + verification.status + ', code ' + (identity.error?.code ?? 'identity'));
  }
  const metricsDir = path.join(root, 'metrics');
  const items = await discoverMedia({ token: credentials.access_token, accountId: credentials.account_id, apiVersion: credentials.api_version, now });
  const snapshots = await readSnapshots(metricsDir);
  const due = dueMedia(items, snapshots, now);
  let target = null;
  let snapshot = snapshots.sort((a, b) => b.collected_at.localeCompare(a.collected_at))[0];
  if (due.length) {
    snapshot = await collectInsights({ token: credentials.access_token, accountId: credentials.account_id, apiVersion: credentials.api_version, now, mediaItems: due });
    target = await saveSnapshot(snapshot, metricsDir, { timestamped: true });
  }
  await regenerateReport(metricsDir, path.join(root, 'context/instagram-performance.md'));
  const status = { checked_at: now.toISOString(), ok: true, collected: due.length > 0, collected_at: snapshot?.collected_at ?? null, discovered_count: items.length, collected_count: due.length, snapshot: target, refresh_warning: refreshWarning ?? null };
  await atomicJson(statusPath, status);
  if (refreshWarning) notify();
  console.log(JSON.stringify(status));
} catch (error) {
  const safeMessage = credentials?.access_token ? error.message.split(credentials.access_token).join('[REDACTED]') : '인증정보 로딩 또는 수집 실패';
  await atomicJson(statusPath, { checked_at: now.toISOString(), ok: false, error: safeMessage });
  notify();
  console.error(safeMessage);
  process.exitCode = 1;
}
