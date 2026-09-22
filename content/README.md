# 콘텐츠

이 폴더를 열고 콘텐츠 일을 시작한다. 기획·대본·Higgsfield 비컷·영상 편집·검수를 한 편 단위로 이어간다.

## 영상 편집을 시작하려면

1. 이 `content` 폴더를 열고 에이전트에게 “영상 편집하자”라고 말한다.
2. 대화에서 정한 작품의 `productions/<작품ID>/inputs`를 Finder로 연다. 대상이 불분명하면 어떤 영상인지 한 번 확인한다.
3. 촬영 원본·참고자료·음원을 넣고 “넣었어”라고 알려준다. 에이전트는 실제 자료 확인 후 승인된 편집·검수로 이어간다.
4. 결과는 해당 작품의 `outputs`에서 확인한다. 폴더 감시나 무인 자동 편집을 설치한 것은 아니다.

## 글로벌 지침은 어디서 읽나

- Codex: `~/.codex/AGENTS.md` → `/Users/kim.kkun/WORKING-AGREEMENTS.md`.
- Claude: `~/.claude/CLAUDE.md` → 같은 글로벌 문서.
- 이 폴더에서도 `AGENTS.md`가 글로벌 문서를 먼저 읽도록 명시한다. `CLAUDE.md`는 `@AGENTS.md`로 같은 업무 지침을 가져온다.
- 일반 MD가 있다는 이유만으로 자동 검색되는 것은 아니다. 지정된 지침 파일에서 연결하기 때문에 읽는다. 새 세션의 실제 로딩은 그 세션에서 확인한다.

## 어디를 보면 되나

- `productions/날짜_소재명/work.md`: 해당 편의 대본·영상·기록과 재개 안내.
- 작품의 `inputs`·`outputs`: 기존 촬영 자료와 검토 결과. 있는 편에만 연결했다.
- `guidelines/`: 단계별로 적용할 기준과 기존 근거.
- `references/ideas`·`성과원본`·`검증대본`: 기존 자료 사본 바로가기.
- `tools/README.md`: 재사용 후보 도구와 실행 전 확인 사항.

## 복사 방식

세 원본 폴더는 `references/legacy-workspace/`에 파일 내용 그대로 복사했다. 위 작품·도구의 바로가기는 원본 Projects가 아니라 이 내부 사본을 가리킨다. 따라서 같은 영상을 다시 복제하지 않는다. 바로가기에서 수정하면 내부 사본이 바뀐다. 기존 원문·수정본은 새 버전으로 보존한다.

이전 폴더 구조는 기존 상대 링크와 도구 전제를 보존하기 위해 남겼다. 새 작품은 `productions/`에 직접 만든다. 기존 Git 이력·Finder 캐시·Python 캐시는 제외했으며 파일별 목록·SHA256 검증은 [복사 확인](references/copy-audit/README.md)에 있다.

CapCut 라이브 프로젝트·연결 서비스·자동 수집 설정은 전환하지 않았다. 옛 문서의 외부 경로나 완료 표시는 현재 실행 증거가 아니다. 이 사본은 같은 컴퓨터 안의 복사이며 외부 백업이 아니다.

## 기존 작품

| 작품 | 가져온 자료 |
|---|---|
| [2026-07-25_kkondae-timing](productions/2026-07-25_kkondae-timing/work.md) | 대본·발행 자료 연결 |
| [2026-07-27_invisible-work](productions/2026-07-27_invisible-work/work.md) | 대본·발행 자료 연결 |
| [2026-07-27_skip-words](productions/2026-07-27_skip-words/work.md) | 대본·발행 자료 연결 |
| [2026-08-03_valley-system](productions/2026-08-03_valley-system/work.md) | 대본·발행 자료 연결 |
| [2026-08-06_checklist-alibi](productions/2026-08-06_checklist-alibi/work.md) | 대본·발행 자료 연결 |
| [2026-08-11_notice-button](productions/2026-08-11_notice-button/work.md) | 대본·발행 자료 연결 |
| [2026-08-16_best-crew-leaves-first](productions/2026-08-16_best-crew-leaves-first/work.md) | 대본·발행 자료 연결 |
| [2026-08-16_beta-recruit](productions/2026-08-16_beta-recruit/work.md) | 대본·발행 자료 연결 |
| [2026-08-19_decision-board](productions/2026-08-19_decision-board/work.md) | 대본·발행 자료 연결 |
| [2026-08-25_two-schedules](productions/2026-08-25_two-schedules/work.md) | 대본·발행 자료 연결 |
| [2026-08-29_beta-recruit-2](productions/2026-08-29_beta-recruit-2/work.md) | 대본·발행 자료 연결 |
| [2026-09-02_phone-only](productions/2026-09-02_phone-only/work.md) | 대본·발행 자료 연결 |
| [2026-09-09_month-end-twice](productions/2026-09-09_month-end-twice/work.md) | 영상 자료 + 대본 연결 |
| [2026-09-11_order-list](productions/2026-09-11_order-list/work.md) | 영상 자료 + 대본 연결 |
| [2026-09-13_owner-three-points](productions/2026-09-13_owner-three-points/work.md) | 영상 자료 + 대본 연결 |
| [2026-09-13_three-causes](productions/2026-09-13_three-causes/work.md) | 영상 자료 + 대본 연결 |
| [2026-09-19_owner-emotions](productions/2026-09-19_owner-emotions/work.md) | 영상 자료 + 대본 연결 |
| [2026-09-21_nagging-environment](productions/2026-09-21_nagging-environment/work.md) | 영상 자료 + 대본 연결 |
