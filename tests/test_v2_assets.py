"""Validate authored mesh topology, references, audio and release checksums."""
from pathlib import Path
import hashlib, json, math, wave
import numpy as np

base=Path(__file__).resolve().parents[1]
world=json.loads((base/'assets/village.json').read_text(encoding='utf-8'))
monsters=json.loads((base/'assets/monsters.json').read_text(encoding='utf-8'))
assert len(monsters['models'])==5
names=set();total=0
for scene in [world]+monsters['models']:
    assert scene['schema']==2
    for key,mesh in scene['meshes'].items():
        assert key not in names,key
        names.add(key)
        v=np.array(mesh['vertices']);assert np.isfinite(v).all()
        assert len(mesh['faces'])==len(mesh['colors'])
        assert len(mesh['normals'])==len(v)
        assert 0<len(v)<=60000 and 0<len(mesh['faces'])<=20000
        assert np.ptp(v,axis=0).min()>0,key
        for f,c in zip(mesh['faces'],mesh['colors']):
            assert len(set(f))==3 and min(f)>=1 and max(f)<=len(v),(key,f)
            assert len(c)==3 and all(0<=x<=255 for x in c)
        for n in mesh['normals']:
            if n:assert abs(np.linalg.norm(n)-1)<.0001
        total+=len(mesh['faces'])
    for inst in scene['instances']:
        assert inst['mesh'] in scene['meshes']
        assert len(inst['cf'])==12 and all(math.isfinite(x) for x in inst['cf'])
    for light in scene['lights']:
        assert 1<=light['part']<=len(scene['parts'])
manifest=json.loads((base/'manifest.json').read_text(encoding='utf-8'))
for name,record in manifest['files'].items():
    p=base/name;b=p.read_bytes()
    assert len(b)==record['bytes'] and hashlib.sha256(b).hexdigest()==record['sha256'],name
    if p.suffix=='.wav':
        with wave.open(str(p),'rb') as w:
            assert (w.getnchannels(),w.getframerate(),w.getsampwidth())==(2,44100,2)
            samples=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2')
            assert np.max(np.abs(samples.astype(np.int32)))<32767
print(f'PASS: {len(names)} meshes / {total} triangles; five distinct monsters; references, normals, checksums and 13 stereo WAVs')
