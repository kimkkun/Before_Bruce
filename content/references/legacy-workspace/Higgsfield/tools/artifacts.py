#!/usr/bin/env python3
"""Local Higgsfield artifact registry. No service calls, uploads, or deletion."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import unquote, urlsplit

RECORD = '생성정보.md'
CUT_RECORD = '제작기록.md'
BASE = Path('99_작업보관/Higgsfield')
BLOCK = re.compile(r'^```json\s*\n(.*?)\n```\s*$', re.M | re.S)
STATES = {'reserved', 'submitted', 'completed', 'failed'}
ASSETS = {'.png', '.jpg', '.jpeg', '.webp', '.mp4', '.mov', '.wav', '.mp3'}

def _link_errors(path):
    if not path.is_file():
        return [f'{path}: missing entry document']
    errors = []
    text = path.read_text(encoding='utf-8')
    for raw in re.findall(r'!?\[[^\]]*\]\(([^\n]+?)\)', text):
        target = raw.strip()
        if target.startswith('<') and '>' in target:
            target = target[1:target.index('>')]
        else:
            target = re.split(r'\s+[\"\']', target, maxsplit=1)[0]
        parsed = urlsplit(target)
        if parsed.scheme or target.startswith('#'):
            continue
        local = path.parent / unquote(parsed.path)
        if parsed.path and not local.exists():
            errors.append(f'{path}: missing linked file: {target}')
    return errors



def read_record(path):
    text = Path(path).read_text(encoding='utf-8')
    matches = list(BLOCK.finditer(text))
    if len(matches) != 1:
        raise ValueError(f'{path}: exactly one JSON record required')
    data = json.loads(matches[0].group(1))
    if not isinstance(data, dict):
        raise ValueError(f'{path}: JSON object required')
    return data


@contextmanager
def _lock(path):
    # Persistent lock inode; do not unlink while another process may hold it.
    p = Path(path)
    if p.is_symlink():
        raise ValueError('symlink lock rejected')
    fd = os.open(p, os.O_CREAT | os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    with os.fdopen(fd, 'a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def _write_unlocked(path, data, create=False):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('symlink record rejected')
    block = '```json\n' + json.dumps(data, ensure_ascii=False, indent=2) + '\n```'
    if create:
        text = '# 생성정보\n\n' + block + '\n\n## 검수\n\n미검수. 사용자 채택 상태는 상위 제작기록에 기록.\n'
        with path.open('x', encoding='utf-8') as handle:
            handle.write(text)
        return
    old = path.read_text(encoding='utf-8')
    read_record(path)
    text = BLOCK.sub(lambda _: block, old, count=1)
    fd, tmp = tempfile.mkstemp(prefix='.record-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def write_record(path, data, create=False):
    """Write only this metadata file; preserve human review prose on updates."""
    path = Path(path)
    with _lock(path.parent / '.record.lock'):
        _write_unlocked(path, data, create)


def _root(path):
    path = Path(path).absolute()
    if path.is_symlink():
        raise ValueError('symlink episode root rejected')
    return path.resolve()


def _inside(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError('nonempty episode-relative path required')
    raw = Path(relative)
    if '..' in raw.parts:
        raise ValueError('path traversal rejected')
    path = root / raw
    if not path.resolve().is_relative_to(root):
        raise ValueError('path escapes episode root')
    return path


def _file_key(path):
    # resolve() alone preserves caller spelling on macOS; stat identifies the
    # actual file without conflating distinct NFC/NFD names on Linux.
    stat = Path(path).stat()
    return (stat.st_dev, stat.st_ino)


def _hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _media_ids(params):
    ids = []
    for media in params.get('medias', []):
        if not isinstance(media, dict):
            raise ValueError('media must be object')
        value = media.get('value')
        if value is None and isinstance(media.get('data'), dict):
            value = media['data'].get('id')
        if not isinstance(value, str) or not value:
            raise ValueError('media reference ID required')
        ids.append(value)
    return ids


def _validate_data(root, path, data, provenance):
    if data.get('schema') != 1 or data.get('kind') not in {'image', 'video'}:
        raise ValueError('schema=1 and kind=image/video required')
    if data.get('status') not in STATES:
        raise ValueError('invalid generation status')
    job = data.get('job_id')
    if job is not None and (not isinstance(job, str) or not job.strip()):
        raise ValueError('invalid job_id')
    if data['status'] in {'submitted', 'completed'} and not job:
        raise ValueError('submitted/completed requires job_id')
    if data['status'] == 'reserved' and job:
        raise ValueError('reserved cannot have job_id')
    if not isinstance(data.get('request_note'), str) or not data['request_note'].strip():
        raise ValueError('approval/budget request_note required')
    params = data.get('params')
    if not isinstance(params, dict) or any(not isinstance(params.get(k), str) or not params[k].strip() for k in ('model', 'prompt')):
        raise ValueError('actual model and prompt required')
    if not isinstance(params.get('medias', []), list):
        raise ValueError('medias must be array')
    inputs = data.get('inputs')
    if not isinstance(inputs, list):
        raise ValueError('inputs array required')
    ids = []
    for item in inputs:
        if not isinstance(item, dict) or not isinstance(item.get('job_id'), str) or not item['job_id']:
            raise ValueError('input job_id required')
        ids.append(item['job_id'])
        external = item.get('external', False)
        if not isinstance(external, bool):
            raise ValueError('external must be boolean')
        source = _inside(root, item.get('path'))
        if not source.is_file() or _hash(source) != item.get('sha256'):
            raise ValueError('input missing or hash mismatch')
        if not external:
            known = provenance.get(_file_key(source))
            if known != item['job_id']:
                raise ValueError('input job provenance mismatch: ' + item['path'])
    if sorted(ids) != sorted(_media_ids(params)):
        raise ValueError('input IDs mismatch params.medias')
    output = data.get('output')
    if data['status'] == 'completed' and not output:
        raise ValueError('completed requires output')
    if output and data['status'] != 'completed':
        raise ValueError('only completed records may have output')
    if output:
        if not isinstance(output, dict):
            raise ValueError('output object required')
        out = _inside(root, output.get('path'))
        if not out.resolve().parent.samefile(path.parent):
            raise ValueError('output must be inside its own version')
        if not out.is_file() or _hash(out) != output.get('sha256'):
            raise ValueError('output missing or hash mismatch')
    if data['status'] == 'failed' and not data.get('failure_reason'):
        raise ValueError('failed requires failure_reason')


def _records(root):
    base = root / BASE
    return sorted(base.glob('*/S*/02_생성버전/v*/' + RECORD))


def _provenance(root):
    result = {}
    for path in _records(root):
        data = read_record(path)
        if data.get('status') == 'completed' and isinstance(data.get('output'), dict):
            result[_file_key(_inside(root, data['output'].get('path')))] = data.get('job_id')
    return result


def validate_episode(root):
    """Return errors without mutations. Does not certify visual quality."""
    root = _root(root)
    errors, jobs, records = [], {}, []
    for name in ('01_자료넣는곳', '02_결과보기', '03_수정기록', '99_작업보관'):
        try:
            if not _inside(root, name).is_dir():
                errors.append(f'{name}: missing canonical directory')
        except ValueError as exc:
            errors.append(str(exc))
    errors.extend(_link_errors(root / 'README.md'))
    shot_ids = {}
    for cut in sorted((root / BASE).glob('*/S*')):
        if not cut.is_dir():
            continue
        if not cut.resolve().is_relative_to(root):
            errors.append(f'{cut}: escaping symlink')
            continue
        shot_id = cut.name.split('_', 1)[0]
        if shot_id in shot_ids:
            errors.append(f'{cut}: duplicate shot ID {shot_id}; existing {shot_ids[shot_id]}')
        shot_ids[shot_id] = cut
        errors.extend(_link_errors(cut / CUT_RECORD))
        for version in sorted((cut / '02_생성버전').glob('v*')):
            path = version / RECORD
            if not path.is_file():
                errors.append(f'{version}: missing {RECORD}')
                continue
            try:
                if not path.resolve().is_relative_to(root):
                    raise ValueError('escaping record symlink')
                records.append((path, read_record(path)))
            except (ValueError, OSError) as exc:
                errors.append(f'{path}: {exc}')
    provenance = {}
    for path, data in records:
        if data.get('status') == 'completed' and isinstance(data.get('output'), dict):
            try:
                provenance[_file_key(_inside(root, data['output'].get('path')))] = data.get('job_id')
            except (ValueError, OSError, TypeError) as exc:
                errors.append(f'{path}: {exc}')
    for path, data in records:
        try:
            _validate_data(root, path, data, provenance)
            if data['status'] in {'completed', 'failed'}:
                registered = (data.get('output') or {}).get('path')
                registered_key = _file_key(_inside(root, registered)) if registered else None
                for asset in path.parent.rglob('*'):
                    if asset.is_file() and asset.suffix.lower() in ASSETS and _file_key(asset) != registered_key:
                        errors.append(f'{asset}: orphan asset not registered as this generation output')
            job = data.get('job_id')
            if job:
                if job in jobs:
                    raise ValueError('duplicate job_id: ' + job)
                jobs[job] = path
        except (ValueError, OSError, TypeError) as exc:
            errors.append(f'{path}: {exc}')
    for path in (root / '03_수정기록').rglob('*'):
        if path.is_file() and path.suffix.lower() in {'.json', '.swift', '.jpg', '.jpeg', '.png'}:
            errors.append(f'{path}: technical artifact belongs in 99_작업보관')
    return errors


def init_episode(root):
    root = _root(root)
    root.mkdir(parents=True, exist_ok=True)
    for name in ('01_자료넣는곳', '02_결과보기', '03_수정기록', '99_작업보관'):
        _inside(root, name).mkdir(exist_ok=True)
    path = root / 'README.md'
    if not path.exists():
        with path.open('x', encoding='utf-8') as handle:
            handle.write('# 영상 작업\n\n현재 상태: 준비. 결과 미생성·사용자 미확정.\n\n- 01_자료넣는곳: 원본\n- 02_결과보기: 최신 검토본\n- 03_수정기록: 대본·사용자 코멘트 연결\n- 99_작업보관: 생성·검수·이전 버전\n')
    return root


def reserve(root, shot, method, request):
    root = _root(root)
    for part in (shot, method):
        if not part or '/' in part or '\\' in part or part in {'.', '..'}:
            raise ValueError('single path component required')
    if not re.fullmatch(r'S\d+[A-Z]?_.+', shot):
        raise ValueError('shot must be S01_name')
    if method not in {'01_내 연기 변환', '02_상황 장면 생성', '03_인물기반 생성'}:
        raise ValueError('unknown method')
    cut = _inside(root, str(BASE / method / shot))
    data = dict(request, schema=1, job_id=None, status='reserved', output=None)
    # Validate before any mkdir or lock file mutation.
    _validate_data(root, cut / '02_생성버전/v001' / RECORD, data, _provenance(root))
    if not root.is_dir():
        raise ValueError('init episode first')
    with _lock(root / '.artifacts.lock'):
        errors = validate_episode(root)
        if errors:
            raise ValueError('existing episode must pass check before reserve: ' + '; '.join(errors))
        shot_id = shot.split('_', 1)[0]
        for existing_cut in (root / BASE).glob('*/S*'):
            if existing_cut.name.split('_', 1)[0] == shot_id and not (cut.exists() and existing_cut.samefile(cut)):
                raise ValueError('shot ID already exists at ' + str(existing_cut))
        versions = cut / '02_생성버전'
        for existing in versions.glob('v*'):
            current = read_record(existing / RECORD)
            if current['status'] in {'reserved', 'submitted'}:
                raise ValueError('pending generation exists; resume or explicitly fail it')
        versions.mkdir(parents=True, exist_ok=True)
        if not (cut / CUT_RECORD).exists():
            with (cut / CUT_RECORD).open('x', encoding='utf-8') as handle:
                handle.write(f'# {shot}\n\n## 현재 상태\n\n준비. 사용자 미확정.\n\n## 장면 설계\n\n대본·장면 목적·통과 기준을 여기에 연결.\n\n## 버전 목록\n\n버전별 입력·출력은 02_생성버전 각 생성정보.md 참조.\n\n## 피드백·검수\n\n미검수.\n')
        n = max([int(p.name[1:]) for p in versions.glob('v*') if re.fullmatch(r'v\d+', p.name)] or [0]) + 1
        version = versions / f'v{n:03d}'
        version.mkdir()  # exclusive reservation while holding episode lock
        write_record(version / RECORD, data, create=True)
        return version / RECORD


def _record_root(path):
    path = Path(path).absolute()
    for root in path.parents:
        if root.name == '99_작업보관':
            episode = _root(root.parent)
            if path.resolve() != path or not path.is_relative_to(episode / BASE):
                raise ValueError('record path or symlink rejected')
            return episode
    raise ValueError('record must be inside episode/99_작업보관/Higgsfield')


def update(path, operation, value, confirmed_failed=False):
    path = Path(path).absolute()
    root = _record_root(path)
    with _lock(root / '.artifacts.lock'):
        with _lock(path.parent / '.record.lock'):
            data = read_record(path)
            if operation == 'bind':
                if data['status'] == 'submitted' and data['job_id'] == value:
                    return
                if data['status'] != 'reserved' or not value.strip():
                    raise ValueError('only reserved jobs can be bound')
                data.update(status='submitted', job_id=value)
            elif operation == 'finish':
                if data['status'] not in {'submitted', 'completed'}:
                    raise ValueError('bind actual job before finish')
                out = Path(value).absolute()
                if not out.resolve().parent.samefile(path.parent):
                    raise ValueError('output must be inside its own version')
                output = {'path': str(out.relative_to(root)), 'sha256': _hash(out)}
                if data['status'] == 'completed' and data['output'] != output:
                    raise ValueError('completed output is immutable')
                data.update(status='completed', output=output)
            elif operation == 'fail':
                if data['status'] not in {'reserved', 'submitted'} or not value.strip():
                    raise ValueError('only reserved/submitted can fail with explicit reason')
                if data['status'] == 'submitted' and not confirmed_failed:
                    raise ValueError('confirm service terminal failure before retry; unknown is not failed')
                data.update(status='failed', failure_reason=value, failure_confirmed=confirmed_failed)
            else:
                raise ValueError('unknown operation')
            _validate_data(root, path, data, _provenance(root))
            if data.get('job_id'):
                for other in _records(root):
                    if other != path and read_record(other).get('job_id') == data['job_id']:
                        raise ValueError('duplicate job_id')
            _write_unlocked(path, data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('init', 'check', 'reserve'):
        p = sub.add_parser(command)
        p.add_argument('root')
        if command == 'reserve':
            p.add_argument('--shot', required=True)
            p.add_argument('--method', required=True)
            p.add_argument('--request', required=True)
    for command, flag in (('bind', 'job-id'), ('finish', 'output'), ('fail', 'reason')):
        p = sub.add_parser(command)
        p.add_argument('record')
        p.add_argument('--' + flag, required=True)
        if command == 'fail':
            p.add_argument('--confirmed-failed', action='store_true', help='operator verified service terminal failure; never use for timeout/unknown')
    args = parser.parse_args()
    try:
        if args.command == 'init':
            print(init_episode(args.root))
        elif args.command == 'reserve':
            print(reserve(args.root, args.shot, args.method, json.loads(Path(args.request).read_text())))
        elif args.command == 'check':
            errors = validate_episode(args.root)
            print('\n'.join(errors) if errors else 'PASS: structure and recorded file references; visual quality not checked')
            return int(bool(errors))
        else:
            update(args.record, args.command, getattr(args, {'bind': 'job_id', 'finish': 'output', 'fail': 'reason'}[args.command]), getattr(args, 'confirmed_failed', False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print('ERROR:', exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
