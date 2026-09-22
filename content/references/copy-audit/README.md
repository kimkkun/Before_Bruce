# 복사·구조화 확인 — 2026-09-22

## 확인한 것

- 기존 김꾼콘텐츠·Higgsfield·김꾼 영상 보관의 파일 792개, 13,882,285,885바이트를 복사했다.
- 원본을 읽으며 계산한 SHA256과 사본 전체를 다시 읽어 계산한 SHA256을 대조했다. 복사 후 구조화에서도 가져온 파일의 본문은 변경하지 않았다.
- 새 작품 18개 입구를 만들었다. 그중 6개에는 기존 영상 자료가 있다. 내부 바로가기 82개는 이 콘텐츠 폴더 안의 사본을 가리킨다.
- 원본 폴더·CapCut 앱·예약 작업·인증정보를 수정하지 않았다. `.git`·`.DS_Store`·`__pycache__`·`.pyc`는 복사하지 않았다. 제외 목록은 manifest에 있다.

## 아직 독립 실행을 확인하지 않은 것

- CapCut 프로젝트 JSON·ZIP 안의 절대경로, 앱의 실제 재열기·편집 복원, 음원·폰트·앱 내 효과 의존성.
- 복사된 설치기·수집기·API 호출·생성·편집 실행. 기존 예약 작업은 기존 위치에서 계속 운영된다.
- 실제 영상 재생·내용 품질·현재 사용자 채택·게시 상태. 과거 검수 기록은 당시 대상에 대한 기록이다.
- 자동보관 `state.json` 원본이 복사 후 갱신된 것을 관찰했다. 사본은 복사 시점 스냅샷이며 실시간 동기화하지 않는다. 후속 원본 변경 목록은 links.json에 있다.

## 옛 문서의 경로

복사된 Markdown의 로컬 링크를 경로 존재 기준으로 검사했다. 웹 URL·문서 내 앵커는 검사하지 않았다. 옛 문서의 링크는 원문 보존을 위해 수정하지 않았으며, 누락 후보는 links.json에 모았다. 원본에서도 없는 링크와 세 원본 폴더 밖 자료를 구분한다.

세 폴더 밖의 개발 정책·과거 Orchestrator·연구 자료는 통째로 가져오지 않았다. 필요할 때 아래 원본을 읽기 전용으로 확인하며, 과거 제품 문서를 현재 정책으로 단정하지 않는다. 이 링크는 다른 작업장의 운영 지침을 자동 적용하라는 뜻이 아니다.

- [new-work.md](</Users/kim.kkun/Projects/Orchestrator/workflows/new-work.md>) — `references/legacy-workspace/Higgsfield/CLAUDE.md`에서 참조
- [index.html](</Users/kim.kkun/Projects/sandbox/ai-workflow-learning/dist/index.html>) — `references/legacy-workspace/Higgsfield/references/2026-09-20_AI워크플로우_조사.md`에서 참조
- [2026-09-21.md](</Users/kim.kkun/Projects/Orchestrator/checks/2026-09-21.md>) — `references/legacy-workspace/김꾼_영상보관/2026-09-21_nagging-environment/03_수정기록/피드백.md`에서 참조
- [CLAUDE.md](</Users/kim.kkun/Projects/the-crew-strategy/CLAUDE.md>) — `references/legacy-workspace/Kim.kkun_contents/CLAUDE.md`에서 참조
- [PRODUCT-RULES.md](</Users/kim.kkun/Projects/the-crew-strategy/planning/PRODUCT-RULES.md>) — `references/legacy-workspace/Kim.kkun_contents/drafts/2026-09-02_phone-only_suhwan-edit.md`에서 참조
- [CUSTOMER-NEEDS.md](</Users/kim.kkun/Projects/the-crew-strategy/planning/CUSTOMER-NEEDS.md>) — `references/legacy-workspace/Kim.kkun_contents/ideas/2026-09-09_phone-only.md`에서 참조
- [PRODUCT-VISION.md](</Users/kim.kkun/Projects/the-crew-strategy/planning/PRODUCT-VISION.md>) — `references/legacy-workspace/Kim.kkun_contents/ideas/2026-09-09_phone-only.md`에서 참조
- [DECISIONS.md](</Users/kim.kkun/Projects/the-crew-strategy/linear/DECISIONS.md>) — `references/legacy-workspace/Kim.kkun_contents/ideas/2026-09-09_phone-only.md`에서 참조
- [DEBT.md](</Users/kim.kkun/Projects/the-crew-strategy/retrospective/v1-docs/DEBT.md>) — `references/legacy-workspace/Kim.kkun_contents/ideas/2026-09-09_phone-only.md`에서 참조
- [inbox.md](</Users/kim.kkun/Projects/ideas/inbox.md>) — `references/legacy-workspace/Kim.kkun_contents/ideas/INDEX.md`에서 참조

## 증거 파일

- [파일별 원본·사본·해시·제외 목록](manifest.json)
- [최초 복사 검증](result.json)
- [최종 사본 무결성·링크·외부 경로 점검](links.json)

같은 Mac 안의 복사이며 외부 백업이 아니다. 새 세션의 실제 지침 적용과 첫 제작 성공은 별도 확인한다.

## 영문 경로 전환 — 2026-09-22

새 작업 입구는 `/Users/kim.kkun/Before_Bruce/content`다. 새 관리 폴더와 파일명만 영문으로 정리했고, `references/legacy-workspace` 안의 원본 사본은 내부 이름과 본문을 보존했다. 예전 manifest.json과 links.json의 경로는 당시 기록이다. 현재 파일 매핑은 [manifest-current.json](manifest-current.json), 영문 변경 후 검증은 [rename-check.json](rename-check.json)에 있다.
