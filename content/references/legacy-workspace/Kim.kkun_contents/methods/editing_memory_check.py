"""Read-only editing memory health check; runs on request, not in the background.
0: no detected problems; 1: warnings/errors; 2: bad invocation.
Character thresholds are review heuristics, not model context/token measurements.
"""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import unquote

CURRENT = '## 현재 상태 — 이 문서가 정본'
HISTORY = '## 과거 이력 — 필요할 때만 조회'


def section(text, start, end=None):
    if start not in text:
        raise ValueError('필수 절 없음: ' + start)
    result = text.split(start, 1)[1]
    return result.split(end, 1)[0] if end else result


def run(repo, episode, current_limit=3500, reading_limit=14000, history_limit=30000):
    repo = Path(repo).resolve()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}_[\w-]+', episode):
        raise ValueError('소재 ID 형식 오류')
    record = repo / 'drafts' / (episode + '_video-comparison.md')
    text = record.read_text()
    findings = []

    def flag(code, detail, level='warning'):
        findings.append({'code': code, 'level': level, 'detail': detail})

    if text.count(CURRENT) != 1:
        flag('current_sections', '현재 상태 정본 절이 정확히 하나여야 함', 'error')
    current = section(text, CURRENT, '## 기록 갱신 방법')
    history = section(text, HISTORY)
    blocks = re.findall(r'```editing-state\s*\n(.*?)\n```', current, re.S)
    if len(blocks) != 1:
        flag('state_metadata', '현재 상태에 검사 메타데이터 하나 필요', 'error')
        state = {}
    else:
        state = json.loads(blocks[0])
    if len(current) > current_limit:
        flag('current_growth', f'현재 상태 {len(current)}자 > 점검 기준 {current_limit}자')
    if len(history) > history_limit:
        flag('history_growth', f'과거 이력 {len(history)}자: 필요한 절만 조회하고 이력 분리 여부 검토')
    for value in re.findall(r'\]\(([^)]+)\)', current):
        base = unquote(value.split('#')[0])
        if base and '://' not in base and not (record.parent / base).exists():
            flag('broken_link', value, 'error')
    workflow = (repo / 'methods/workflow.md').read_text()
    style = (repo / 'methods/capcut-caption-style.md').read_text()
    automation = (repo / 'methods/automation.md').read_text()
    active = [current,
              section(workflow, '## 영상 편집 세션', '## 발행 후'),
              section(style, '## 적용할 기준과 과거 사례 구분', '## 최신 연출 참조'),
              section(automation, '### 단계별 실행 확인 — 2026-09-19', '### 글씨 크기')]
    for name in ['context/kimkkun-mind.md', 'context/audience.md']:
        active.append((repo / name).read_text())
    characters = sum(map(len, active))
    if characters > reading_limit:
        flag('reading_growth', f'선택한 기본 읽기 범위 {characters}자 > {reading_limit}자: 중복/과거 사례 로드 검토')
    baseline = state.get('baseline', {})
    if not baseline.get('path') or not baseline.get('sha256'):
        flag('baseline_missing', '비교 기준 프로젝트 묶음과 고정 해시가 필요함', 'error')
    else:
        path = (record.parent / baseline['path']).resolve()
        if not path.is_file():
            flag('baseline_missing', str(path), 'error')
        else:
            h = hashlib.sha256()
            with path.open('rb') as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b''):
                    h.update(chunk)
            if h.hexdigest() != baseline['sha256']:
                flag('baseline_changed', '비교 기준 파일 내용이 바뀜. 라이브 프로젝트를 덮어쓰지 말고 기준 확인', 'error')
            try:
                with zipfile.ZipFile(path) as z:
                    json.loads(z.read('draft_info.json'))
            except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
                flag('baseline_unreadable', str(error), 'error')
    feedback = state.get('feedback', [])
    seen, agreed = set(), {}
    pending = []
    for item in feedback:
        identity = item.get('id')
        if not identity or identity in seen:
            flag('feedback_id', str(identity), 'error')
        seen.add(identity)
        if not item.get('source'):
            flag('feedback_source', str(identity) + ': 사용자 발언·출처 누락')
        status = item.get('status')
        if status not in ['pending', 'applied', 'deferred']:
            flag('feedback_status', str(identity) + ': 상태 누락/오류', 'error')
        if status == 'pending':
            pending.append(identity)
        if status == 'applied':
            evidence = item.get('evidence')
            if not evidence or not (record.parent / evidence.split('#')[0]).exists():
                flag('applied_without_evidence', str(identity) + ': 반영 근거 파일 없음', 'error')
        if item.get('scope') == 'common':
            if item.get('confirmed') is not True:
                flag('unconfirmed_promotion', str(identity) + ': 미확정 피드백을 공통 기준으로 승격', 'error')
            if status == 'applied' and not item.get('rule_anchor'):
                flag('rule_not_linked', str(identity) + ': 공통 기준 반영 절 누락')
            anchor = item.get('rule_anchor')
            if anchor and anchor not in style:
                flag('rule_not_linked', str(identity) + ': 공통 기준의 실제 절을 찾지 못함')
            key = item.get('property')
            if key and item.get('confirmed') is True and status != 'deferred':
                value = json.dumps(item.get('value'), ensure_ascii=False, sort_keys=True)
                if key in agreed and agreed[key] != value:
                    flag('conflicting_feedback', key + ': 확정된 공통 피드백 값 충돌', 'error')
                agreed[key] = value
    if state.get('review_state') not in ['awaiting_user', 'reviewing', 'ready']:
        flag('review_state', 'awaiting_user/reviewing/ready 중 상태 필요', 'error')
    if state.get('review_state') == 'ready' and pending:
        flag('pending_at_delivery', '완료 상태에 미반영 코멘트: ' + ', '.join(pending), 'error')
    library = repo.parent / '김꾼_영상보관' / episode
    results = library / '02_결과보기'
    files = [p for p in results.iterdir() if p.is_file() and not p.name.startswith('.')] if results.exists() else []
    videos = [p for p in files if p.suffix.lower() in ['.mov', '.mp4', '.m4v']]
    images = [p for p in files if p.suffix.lower() in ['.png', '.jpg', '.jpeg']]
    if len(videos) > 1 or len(images) > 1 or len(files) != len(videos) + len(images):
        flag('result_clutter', '결과보기는 최신 영상 1개·썸네일 1개만 유지')
    if state.get('review_state') == 'ready' and (len(videos), len(images)) != (1, 1):
        flag('missing_results', '전달 완료인데 영상 또는 썸네일 없음', 'error')
    pointer = library / '03_수정기록/README.md'
    if not pointer.exists() or record.name not in pointer.read_text():
        flag('record_pointer', '수정기록 입구가 정본을 가리키지 않음', 'error')
    return {'ok': not findings, 'findings': findings, 'pending_feedback': pending,
            'metrics': {'current_characters': len(current), 'selected_reading_characters': characters,
                        'history_characters': len(history)},
            'limits': '실제 대화 토큰·전체 시스템 프롬프트·의미상 모든 충돌·기록하지 않은 코멘트·편집 품질은 자동 판정하지 않음. 대화 밖 상시 알림 없음.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--episode', required=True)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        result = run(args.repo, args.episode)
    except (OSError, ValueError, TypeError, AttributeError) as error:
        print(json.dumps({'ok': False, 'error': str(error)}, ensure_ascii=False))
        raise SystemExit(2)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['ok'] else 1)
