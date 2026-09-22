#!/bin/zsh
# 기존 영상 편집 전용 프로필로 새 대화를 연다. 다른 세션 권한은 변경하지 않는다.
set -eu
CODEX_VIDEO_BIN=/opt/homebrew/bin/codex
CODEX_VIDEO_ROOT=/Users/kim.kkun/Projects
if [[ ! -x "$CODEX_VIDEO_BIN" || ! -f /Users/kim.kkun/.codex/video-edit.config.toml ]]; then
  print '영상 편집 실행 파일 또는 전용 설정을 찾지 못했어. Codex에 이 메시지를 알려줘.'
  read '?Enter를 누르면 닫혀.'
  exit 1
fi
cd "$CODEX_VIDEO_ROOT"
print '영상 편집 전용 대화를 시작해. 열린 창에 “○○ 폴더 자료로 편집해”라고 입력하면 돼.'
exec "$CODEX_VIDEO_BIN" --profile video-edit -C "$CODEX_VIDEO_ROOT"
