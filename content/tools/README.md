# 기존 도구 사본

바로가기는 Before_Bruce 안의 사본을 가리킨다. Python·Node 파일은 복사했지만 실행·설치·인증·예약 작업 전환은 하지 않았다.

| 도구 | 용도 | 실행 전 확인 |
|---|---|---|
| `Higgsfield/tools/artifacts.py` | 컷·버전·job·파일 참조 등록 및 검사 | 템플릿 README와 명시한 작품 루트 |
| `편집과성과/capcut_check.py` | CapCut 파일 참조·출력명 검사 | 실제 프로젝트 JSON·출력의 절대경로 |
| `편집과성과/editing_memory_check.py` | 기존 편집 기록 상태 검사 | `--repo`는 사본 Kim.kkun_contents, 대상 편의 실제 자료 경로 |
| `편집과성과/capcut-archive/` | 기존 자동 보관 프로그램 | 설치하지 않음. 기본값에 홈 Movies 경로가 있으므로 원본 대상 여부 확인 |
| `편집과성과/instagram-insights*.mjs` | 성과 수집 | 기존 예약 작업·인증은 원래 환경에 유지. 복사본에서 중복 실행하지 않음 |

원본 도구를 실행하거나 기존 서비스를 변경한 것으로 보고하지 않는다. 새 작품 구조와의 호환성은 첫 사용 시 실제 입력으로 확인한다.

## 자료 폴더 열기

`python3 tools/open_inputs.py <작품ID>`는 선택한 작품의 inputs만 Finder로 연다. 없는 inputs는 해당 작품 안에 만든다. 작품 자동 선택은 하지 않는다. `--print-only`는 생성·열기 없이 경로만 검증한다.
