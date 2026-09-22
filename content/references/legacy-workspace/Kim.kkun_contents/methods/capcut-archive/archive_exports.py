#!/usr/bin/python3
"""Read-only CapCut export collection. Run once per minute via launchd."""
import argparse, datetime, fcntl, hashlib, json, os, re, shutil, time, zipfile
from pathlib import Path

EXTS = {'.mov', '.mp4', '.m4v'}

def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()

def signature(p):
    s = p.stat()
    return [s.st_size, s.st_mtime_ns]

def save(path, data):
    tmp = path.with_suffix('.pending')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    os.replace(tmp, path)

def project_snapshot(project, target):
    """Capture current project and referenced resources; not proof of export provenance."""
    source = project / 'draft_info.json'
    raw = source.read_bytes()
    doc = json.loads(raw)
    paths = set()
    def walk(v):
        if isinstance(v, dict):
            for x in v.values(): walk(x)
        elif isinstance(v, list):
            for x in v: walk(x)
        elif isinstance(v, str):
            if v.startswith('##_draftpath_placeholder_') and '_##/' in v:
                paths.add(str(project / v.split('_##/', 1)[1]))
            elif v.startswith('/'): paths.add(v)
            elif v.startswith('{'):
                try: walk(json.loads(v))
                except ValueError: pass
    walk(doc)
    files, missing = {}, []
    for name in sorted(paths):
        p = Path(name)
        if p.is_file(): files[str(p)] = p
        elif p.is_dir():
            for f in p.rglob('*'):
                if f.is_file(): files[str(f)] = f
        else: missing.append(name)
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_STORED) as z:
        z.writestr('draft_info.json', raw)
        for name, p in sorted(files.items()): z.write(p, 'files/' + name.lstrip('/'))
        z.writestr('snapshot-note.json', json.dumps({'captured_at':datetime.datetime.now().isoformat(), 'missing_paths':missing, 'export_correspondence':'current project snapshot, not verified against rendered export'}, ensure_ascii=False))
    return {'file':target.name,'missing_paths':missing,'project':str(project),'draft_sha256':hashlib.sha256(raw).hexdigest()}

def exports(source):
    for folder, dirs, names in os.walk(source):
        dirs[:] = [n for n in dirs if n != "User Data" and not n.startswith(".")]
        for name in sorted(names):
            p = Path(folder) / name
            if p.suffix.lower() in EXTS: yield p

def run(source, root, projects, settle=60):
    support = root / '99_관리자료' / '자동보관'
    support.mkdir(parents=True, exist_ok=True)
    with (support / 'collector.lock').open('a') as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: return
        statepath = support / 'state.json'
        state = json.loads(statepath.read_text()) if statepath.exists() else {'observed':{},'archived':{}}
        errors=[]
        for p in sorted(exports(source)) if source.exists() else []:
            if not p.is_file() or p.suffix.lower() not in EXTS: continue
            try:
                folders=[d for d in root.iterdir() if d.is_dir() and re.match(r'^\d{4}-\d{2}-\d{2}_',d.name) and (d/'01_자료넣는곳').is_dir() and (p.stem==d.name or p.stem.startswith(d.name+'_'))]
                matched=max(folders,key=lambda d:len(d.name)) if folders else None
                if matched is None: continue
                sig=signature(p); key=str(p); old=state['observed'].get(key)
                if old and old.get('done') == sig: continue
                if not old or old['signature'] != sig:
                    state['observed'][key]={'signature':sig,'since':time.time()};continue
                if time.time()-old['since']<settle or time.time()-p.stat().st_mtime<settle: continue
                sha=digest(p)
                if signature(p)!=sig: continue
                if sha in state['archived']:
                    saved=Path(state['archived'][sha]['video'])
                    if saved.exists() and digest(saved)==sha:
                        old['done']=sig;continue
                destination=matched/'99_작업보관'/'자동보관'
                stamp=datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime('%Y%m%d-%H%M%S')
                version=destination/(p.stem+'__'+stamp+'__'+sha[:12]);version.mkdir(parents=True,exist_ok=True)
                final=version/p.name
                if not final.exists() or digest(final)!=sha:
                    pending=version/(p.name+'.partial');shutil.copy2(p,pending)
                    if signature(p)!=sig or digest(pending)!=sha: continue
                    os.replace(pending,final)
                record={'source':str(p),'source_signature':sig,'video':str(final),'sha256':sha,'archived_at':datetime.datetime.now().isoformat(),'classification':matched.name if matched else 'unclassified','publication_status':'unknown','project_snapshot':None}
                names=[p.stem,re.sub(r'\(\d+\)$','',p.stem)]
                project_roots=[projects, p.parent/'User Data/Projects/com.lveditor.draft']
                candidate=next((pr/name for pr in project_roots for name in names if (pr/name/'draft_info.json').exists()),None)
                if candidate:
                    z=version/'capcut-project-resources.zip'
                    try:
                        note=project_snapshot(candidate,version/'capcut-project-resources.partial')
                        os.replace(version/'capcut-project-resources.partial',z);note['file']=z.name;record['project_snapshot']=note
                    except Exception as e: record['project_snapshot_error']=str(e)
                save(version/'manifest.json',record)
                state['archived'][sha]=record;old['done']=sig
                print('ARCHIVED',p.name,'->',final,flush=True)
            except Exception as e:
                errors.append({'source':str(p),'error':str(e)});print('ERROR',p,str(e),flush=True)
        state['last_scan']=datetime.datetime.now().isoformat();state['last_errors']=errors
        save(statepath,state)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=Path.home()/'Movies/CapCut');ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[3]/'김꾼_영상보관');ap.add_argument('--projects',type=Path,default=Path.home()/'Movies/CapCut/User Data/Projects/com.lveditor.draft');ap.add_argument('--settle',type=int,default=60);a=ap.parse_args();run(a.source,a.root,a.projects,a.settle)
