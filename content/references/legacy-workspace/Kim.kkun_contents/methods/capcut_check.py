"""Read-only CapCut path/export checks. JSON stdout; 0=pass, 1=issues, 2=input error.

This checks saved JSON, not live UI, media decoding, or restoration completeness.
"""
import argparse
import json
import re
from pathlib import Path


def check(project, episode, export=None):
    project = Path(project).resolve(strict=True)
    data = json.loads(project.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("tracks"), list):
        raise ValueError("타임라인 tracks가 있는 프로젝트 JSON을 지정해야 함")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}_[\w-]+", episode):
        raise ValueError("소재 ID는 YYYY-MM-DD_소재ID 형식이어야 함")
    refs, unknown = set(), set()

    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if isinstance(item, str) and item and (key == "path" or key.endswith("_path")):
                    if item.startswith(("http://", "https://")):
                        unknown.add(item)
                        continue
                    resolved = re.sub(r"^##_draftpath_placeholder_[^/]+_##/?", "", item)
                    if "##_draftpath_placeholder_" in resolved or "://" in resolved:
                        unknown.add(item)
                        continue
                    path = Path(resolved).expanduser()
                    refs.add(str((path if path.is_absolute() else project.parent / path).resolve()))
                elif isinstance(item, (dict, list)):
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(data)
    missing = sorted(p for p in refs if not Path(p).exists())
    issues = []
    if missing:
        issues.append("저장 JSON의 참조 경로 누락: 사용 재료인지 확인 후 복구")
    if unknown:
        issues.append("해석하지 못한 참조 경로: 수동 확인 필요")
    audio_ids = {}
    materials = data.get("materials", {})
    for material in (materials.get("audios", []) if isinstance(materials, dict) else []):
        effect = material.get("effect_id")
        if effect:
            audio_ids.setdefault(effect, set()).add(material.get("name", ""))
    collisions = {key: sorted(names) for key, names in audio_ids.items() if len(names) > 1}
    if collisions:
        issues.append("하나의 음향 effect_id에 서로 다른 이름이 연결됨: 원음·재열기 후 연결 대조 필요")
    result = {"project": str(project), "references": sorted(refs), "missing": missing,
              "audio_identity_conflicts": collisions,
              "unresolved": sorted(unknown), "issues": issues,
              "limits": "경로 존재는 CapCut 로드 성공·ZIP 복원·영상 품질을 보증하지 않음"}
    if export is not None:
        output = Path(export).expanduser().resolve()
        valid_name = bool(re.fullmatch(re.escape(episode) + r"_v\d{3,}\.(mov|mp4|m4v)", output.name, re.I))
        exists = output.is_file() and output.stat().st_size > 0
        result["export"] = {"path": str(output), "name_matches": valid_name, "nonempty_file": exists}
        if not valid_name:
            issues.append("출력명 불일치: 소재 ID와 버전을 실제 파일명에서 확인")
        if not exists:
            issues.append("출력 영상이 없거나 비어 있음")
    result["ok"] = not issues
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="실제 draft_info.json 또는 draft_content.json")
    parser.add_argument("--episode", required=True)
    parser.add_argument("--export", help="전달 사본이 아닌 CapCut 최초 출력 파일")
    args = parser.parse_args()
    try:
        result = check(args.project, args.episode, args.export)
    except (OSError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
