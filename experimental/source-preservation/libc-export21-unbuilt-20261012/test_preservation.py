"""Portable source checks; no compiler, adoption, Wine, or device actions."""
import ast,hashlib,json,re,struct,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
MANIFEST=json.loads((HERE/'source-manifest.json').read_text());PROVENANCE=json.loads((HERE/'provenance.json').read_text());GUARD=MANIFEST['guardPrefix'];DEF='core/libs/prx/libc/src/specifics/windows/compiler_once_exports.def'
def functions():
 source=(HERE/'snapshots/check_libc_exports.py.snapshot').read_text();assert source.startswith(GUARD)
 tree=ast.parse(source[len(GUARD):]);nodes=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.Assign))]
 scope={'__name__':'synthetic_parser'};exec(compile(ast.Module(body=nodes,type_ignores=[]),'<synthetic-source-check>','exec'),scope);return scope

def old_def():
 source=(ROOT/'patches/anyps5/0012-native-compiler-once.patch').read_text();marker=f'+++ b/{DEF}\n';part=source.split(marker,1)[1].split('\ndiff --git ',1)[0]
 return ''.join(line[1:]+'\n' for line in part.splitlines() if line.startswith('+') and not line.startswith('+++'))

def synthetic_pe():
 data=bytearray(0x600)
 def u16(at,v):struct.pack_into('<H',data,at,v)
 def u32(at,v):struct.pack_into('<I',data,at,v)
 data[:2]=b'MZ';u32(0x3c,0x80);data[0x80:0x84]=b'PE\0\0';u16(0x86,1);u16(0x94,0xf0)
 opt=0x98;u16(opt,0x20b);u32(opt+112,0x1000);u32(opt+116,0x200);section=opt+0xf0
 for off,v in [(8,0x400),(12,0x1000),(16,0x400),(20,0x200)]:u32(section+off,v)
 for off,v in [(16,1),(20,3),(24,3),(28,0x1040),(32,0x1060),(36,0x1080)]:u32(0x200+off,v)
 for i in range(3):u32(0x240+i*4,0x1200+i)
 at=0x300
 for i,name in enumerate(('beta','alpha','public_data')):
  raw=name.encode()+b'\0';data[at:at+len(raw)]=raw;u32(0x260+i*4,0x1000+at-0x200);u16(0x280+i*2,(1,0,2)[i]);at+=len(raw)
 return data

class PreservationTests(unittest.TestCase):
 def test_hashes_guards_syntax(self):
  for relative,record in MANIFEST['sourceFiles'].items():
   raw=(HERE/relative).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),record['snapshotSha256']);self.assertTrue(raw.startswith(GUARD.encode()));normalized=raw[len(GUARD.encode()):]
   self.assertEqual(hashlib.sha256(normalized).hexdigest(),record['normalizedSha256']);self.assertIsInstance(ast.parse(raw).body[0],ast.Raise);ast.parse(normalized)
  self.assertFalse(MANIFEST['sourceSnapshotsExecuted'])
 def test_privacy_text_only(self):
  local='/'+'Users'+'/';credential=re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)')
  for path in HERE.rglob('*'):
   if not path.is_file():continue
   self.assertFalse(path.is_symlink());self.assertEqual(path.stat().st_mode&0o111,0);self.assertIn(path.suffix,{'.snapshot','.patch','.json','.md','.py'})
   raw=path.read_bytes();text=raw.decode('utf-8');self.assertFalse(raw.startswith(b'MZ'));self.assertNotIn(local,text);self.assertIsNone(credential.search(text))
 def test_patch_exact_scope_and_ordinals(self):
  relative,expected=next(iter(MANIFEST['patches'].items()));patch=(HERE/relative).read_text();self.assertEqual(hashlib.sha256(patch.encode()).hexdigest(),expected);self.assertEqual(expected,'3ab16362f8068afc18c90acc414764932a5ed6026184f5ae125e5fa7a923c1f4')
  self.assertEqual(re.findall(r'^--- a/(.*)$',patch,re.M),[DEF]);self.assertEqual(re.findall(r'^\+\+\+ b/(.*)$',patch,re.M),[DEF]);self.assertFalse(any(x.startswith('-') and not x.startswith('---') for x in patch.splitlines()))
  added=[x[1:] for x in patch.splitlines() if x.startswith('+') and not x.startswith('+++')];rows=[re.fullmatch(r'  "([^"]+)" @(\d+)',x) for x in added]
  self.assertTrue(all(rows));self.assertEqual(len(rows),12);self.assertEqual([int(x[2]) for x in rows],list(range(1063,1075)));self.assertEqual([x[1] for x in rows],sorted(PROVENANCE['newImplementedPublicCExports']))
  before=old_def();self.assertEqual(hashlib.sha256(before.encode()).hexdigest(),'1631998a69997f05bed054ba12f5df9a3b937ce72524350b8191b97985225af3');self.assertEqual(sum(x.endswith(' DATA') for x in before.splitlines()),149)
  self.assertIn('  APS5NativeCompilerOnce_nid_no_patch @1062\n',before)
  with tempfile.TemporaryDirectory() as tmp:
   original=Path(tmp)/'old.def';candidate=Path(tmp)/'new.def';original.write_text(before);candidate.write_text(before+'\n'.join(added)+'\n');parse=functions()['declarations'];old=parse(original);new=parse(candidate)
   self.assertEqual(len(old),1062);self.assertEqual(len(new),1074);self.assertTrue(all(new[n]==o for n,o in old.items()))
 def test_unbuilt_unapplied_scope(self):
  for name in ('patch21AppliedToCanonicalOrPrivate20','patch21Compiled','patch21PostbuildExportOrNidClosureQualified','fullHleQualified','deviceExecuted','gameplayVerified'):self.assertFalse(PROVENANCE[name])
  self.assertTrue(PROVENANCE['knownMsaaPolicyBoundaryNotResolved']);self.assertEqual(PROVENANCE['inlineCppHelperExcluded'],'ResolvePathError_nid_no_patch')
 def test_data_and_duplicate_def_rows(self):
  parse=functions()['declarations']
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'test.def';p.write_text('LIBRARY libc.prx\nEXPORTS\n  "public_data" @1 DATA\n  "function" @2\n');self.assertEqual(parse(p),{'public_data':1,'function':2})
   for rows in ('  "a" @1\n  "a" @2\n','  "a" @1\n  "b" @1\n','  "a" @1 NONAME\n'):
    p.write_text('LIBRARY libc.prx\nEXPORTS\n'+rows)
    with self.assertRaises(ValueError):parse(p)
 def test_synthetic_pe_actual_name_ordinals(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'synthetic.pe';p.write_bytes(synthetic_pe());self.assertEqual(functions()['exports'](p),{'beta':2,'alpha':1,'public_data':3})
 def test_synthetic_pe_bounds(self):
  parse=functions()['exports']
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'synthetic.pe';data=synthetic_pe();struct.pack_into('<H',data,0x280,4);p.write_bytes(data)
   with self.assertRaises(ValueError):parse(p)
   data=synthetic_pe();struct.pack_into('<I',data,0x260,0x5000);p.write_bytes(data)
   with self.assertRaises(ValueError):parse(p)

if __name__=='__main__':unittest.main()
