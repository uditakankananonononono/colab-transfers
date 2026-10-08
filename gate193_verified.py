import os, csv, hashlib, zipfile, struct, io, re, json
from pathlib import Path
import numpy as np
from collections import Counter,defaultdict
root=Path('/content'); zpath=root/'1-193-manifests-for-colab.zip'
EXP={'all_npy_manifest.tsv':'b7bf1e20234d6254c68a72bbd04f1926ab95a87de9d3f7b8751b9518ed24239f','fold_assignments.csv':'a56e946975aaa98b23a686c3ce762857ce48ded2e3595a4f187beffed22da960','random_assignments.csv':'cc0cedde458ec0ddaad16949774a62a6505cc64e4cd016f4ba8cce5f97d56e58'}
with zipfile.ZipFile(zpath) as z:
 for n,h in EXP.items():
  b=z.read(n); got=hashlib.sha256(b).hexdigest(); assert got==h,(n,got,h)
  (root/n).write_bytes(b)
print('manifest hash validation: PASS')
rows=list(csv.DictReader(open(root/'all_npy_manifest.tsv',newline=''),delimiter='\t'))
print('all-npy row count',len(rows),'uncompressed total',sum(int(r['uncompressed_bytes']) for r in rows),'compressed total',sum(int(r['compressed_bytes']) for r in rows))
fold=list(csv.DictReader(open(root/'fold_assignments.csv',newline='')))
rand=list(csv.DictReader(open(root/'random_assignments.csv',newline='')))
print('fold assignment rows',len(fold),'random assignment rows',len(rand))
assert len(rows)==25449 and sum(int(r['uncompressed_bytes']) for r in rows)==5900117472
assert len(fold)==25449 and len(rand)==25449*5
# Verify IDs and labels, assignment counts by split; pre-outcome gates.
assert [r['filename'] for r in rows]==sorted(r['filename'] for r in rows)
for r in rows:
 stem=Path(r['filename']).stem; cl=stem.split('__')[-1]
 assert cl in {'0','2','3','4','5'},(r['filename'],cl)
# Expected shapes and dtype read from actual 128-byte NPY v1 header (manifest sizes determine header)
shape_counts=Counter(); subj_windows=Counter(); class_counts=Counter(); maxT=0; expected_by_name={r['filename']:r for r in rows}
for i,r in enumerate(rows):
 n=r['filename']; assert int(r['compression'])==8
 # Verify header templates from manifest's exact expected byte lengths: actual payload read later in extraction.
 t=(int(r['uncompressed_bytes'])-128)//(29*4)
 assert int(r['uncompressed_bytes'])==128+29*t*4
 assert t in (500,1000,1500,2000); maxT=max(maxT,t); shape_counts[t]+=1
print('manifest length census',dict(sorted(shape_counts.items())),'maxT',maxT)
# Assignment counts exact and consistency with precomputed forms.
fby=defaultdict(Counter)
for r in fold:
 f=int(r['group_fold']); fby[f][(r['label'])]+=1
print('fold windows', {f:(sum(c.values()), c.get('1',0),c.get('0',0)) for f,c in fby.items()})
rf=defaultdict(Counter)
for r in rand: rf[(int(r['seed']),r['partition'])][r['label']]+=1
print('random split windows',{k:(sum(c.values()),c.get('1',0),c.get('0',0)) for k,c in sorted(rf.items())})
# Check each file identity and patient label align with inventories, validate counts
assert len({r['filename'] for r in fold})==25449
assert len({r['filename'] for r in rand})==25449*5
assert all(r['filename'] in expected_by_name and r['patient_id']==Path(r['filename']).stem.split('_')[0] and r['label']==('0' if Path(r['filename']).stem.split('__')[-1]=='0' else '1') and 1<=int(r['group_fold'])<=5 for r in fold)
for seed in (19342,19343,19344,19345,19346):
 sr=[r for r in rand if int(r['seed'])==seed]; assert len(sr)==25449 and len({r['filename'] for r in sr})==25449
 assert all(r['filename'] in expected_by_name and r['patient_id']==Path(r['filename']).stem.split('_')[0] and r['label']==('0' if Path(r['filename']).stem.split('__')[-1]=='0' else '1') for r in sr)
 assert sum(r['partition']=='test' for r in sr)==5089 and sum(r['partition']=='train' for r in sr)==20360
print('pre-outcome manifest structure and expected-byte gates PASS; extraction and per-member checksum pending')
