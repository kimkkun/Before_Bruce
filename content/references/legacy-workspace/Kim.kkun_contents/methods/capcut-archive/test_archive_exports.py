import tempfile,pathlib,json
ns={'__name__':'test'};script=pathlib.Path(__file__).with_name('archive_exports.py');exec(compile(script.read_text(),str(script),'exec'),ns)
b=pathlib.Path(tempfile.mkdtemp(prefix='capcut-archive-test-'));src=b/'exports';root=b/'archive';proj=b/'projects';src.mkdir();root.mkdir();proj.mkdir();(root/'2026-09-19_test'/'01_자료넣는곳').mkdir(parents=True);f=src/'2026-09-19_test_v001.mov';f.write_bytes(b'first export')
run=lambda:ns['run'](src,root,proj,0)
run();assert not list(root.rglob('*.mov'))
run();assert len(list(root.rglob('*.mov')))==1
run();assert len(list(root.rglob('*.mov')))==1
f.write_bytes(b'second export');run();run();assert len(list(root.rglob('*.mov')))==2
unknown=src/'unknown.mp4';unknown.write_bytes(b'unknown');run();run();assert not list(root.rglob('unknown.mp4'))
assert f.read_bytes()==b'second export';assert {p.read_bytes() for p in root.rglob('*.mov')}=={b'first export',b'second export'}
print('PASS: settle, dedup, overwrite versioning, unknown exclusion, source preservation')
nested=src/'organized';nested.mkdir();(nested/'nested.mov').write_bytes(b'nested');cache=nested/'User Data';cache.mkdir();(cache/'ignore.mov').write_bytes(b'cache');run();run();assert not list(root.rglob('nested.mov'));assert not list(root.rglob('ignore.mov'))
project=proj/'project';project.mkdir();asset=b/'asset.wav';asset.write_bytes(b'asset');(project/'draft_info.json').write_text(json.dumps({'materials':{'audios':[{'path':str(asset)}]}}));record=ns['project_snapshot'](project,b/'test.zip');assert not record['missing_paths'];print('PASS: nested folder, User Data exclusion, project resource bundle')
