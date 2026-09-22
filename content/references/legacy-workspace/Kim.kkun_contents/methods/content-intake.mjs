#!/usr/bin/env node
// Register source files without moving, editing, deleting, or uploading them.
import { createHash } from 'node:crypto';
import { createReadStream } from 'node:fs';
import { stat, readFile, writeFile, realpath } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

async function describeFile(filename, extensions) {
  const resolved = await realpath(filename);
  if (!extensions.includes(path.extname(resolved).toLowerCase())) throw new Error('지원하지 않는 파일 형식: ' + resolved);
  const before = await stat(resolved);
  if (!before.isFile() || before.size === 0) throw new Error('비어 있지 않은 파일이 필요해: ' + resolved);
  const hash = createHash('sha256');
  for await (const chunk of createReadStream(resolved)) hash.update(chunk);
  const after = await stat(resolved);
  if (before.size !== after.size || before.mtimeMs !== after.mtimeMs) {
    throw new Error('아직 복사·수정 중인 파일이야. 완료된 뒤 다시 등록해줘.');
  }
  return { path: resolved, bytes: after.size, modified_at: after.mtime.toISOString(), sha256: hash.digest('hex') };
}

export async function registerContent({ videoPath, scriptPath, outputDir, now = new Date() }) {
  const video = await describeFile(videoPath, ['.mp4', '.mov', '.m4v', '.mxf']);
  const script = await describeFile(scriptPath, ['.md', '.txt']);
  if (script.bytes > 1_000_000) throw new Error('대본 파일은 1MB 이하로 지정해줘.');
  const scriptText = await readFile(script.path, 'utf8');
  if (createHash('sha256').update(scriptText).digest('hex') !== script.sha256) {
    throw new Error('대본이 등록 도중 바뀌었어. 다시 등록해줘.');
  }
  const id = video.sha256.slice(0, 16) + '-' + script.sha256.slice(0, 12);
  const manifest = {
    schema_version: 1,
    content_id: id,
    registered_at: now.toISOString(),
    source_video: video,
    script_snapshot: { ...script, text: scriptText },
    transcript: null,
    editor: { application: 'Palmier Pro', project_path: null, timeline_id: null },
    edit_recipe: null,
    final_video: null,
    instagram: { account: 'kim.kkun', media_id: null, permalink: null },
    status: 'registered_only',
    pending: ['transcription', 'rough_cut', 'Palmier_validation', 'publication_link'],
  };
  const target = path.join(outputDir, 'content-' + id + '.json');
  try {
    await writeFile(target, JSON.stringify(manifest, null, 2) + '\n', { flag: 'wx', mode: 0o600 });
    return { path: target, created: true, content_id: id };
  } catch (error) {
    if (error.code !== 'EEXIST') throw error;
    const existing = JSON.parse(await readFile(target, 'utf8'));
    if (existing.source_video?.sha256 !== video.sha256 || existing.script_snapshot?.sha256 !== script.sha256) {
      throw new Error('기존 콘텐츠 기록과 파일 해시가 일치하지 않아.');
    }
    return { path: target, created: false, content_id: id };
  }
}

async function main() {
  const [videoPath, scriptPath] = process.argv.slice(2);
  if (!videoPath || !scriptPath) throw new Error('사용법: node methods/content-intake.mjs 원본영상경로 대본경로');
  const result = await registerContent({
    videoPath, scriptPath, outputDir: path.join(projectRoot, 'drafts'),
  });
  console.log(JSON.stringify({ ...result, edited: false, uploaded: false }, null, 2));
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(error => { console.error(error.message); process.exitCode = 1; });
}
