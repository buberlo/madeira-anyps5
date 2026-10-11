"""Compile/run only isolated native harnesses; no FEX build, signing or device calls."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import signal
import subprocess
import time
import importlib.util

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stat(p):
 s=Path(p).stat();return [s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def qualify(output, fex_source, wine_signal, wine_unwind, compiler, sdk):
 fex_source, wine_signal, wine_unwind, CLANG, SDK = map(Path, (fex_source, wine_signal, wine_unwind, compiler, sdk))
 output=Path(output).absolute();output.mkdir(exist_ok=False)
 spec=importlib.util.spec_from_file_location('native_extract',HERE/'extract_harness.py')
 e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
 sources=output/'sources';e.generate(sources, fex_source, wine_signal, wine_unwind)
 inputs={str(p):sha(p) for p in [CLANG,HERE/'extract_harness.py',HERE/'native-adapter.hpp',HERE/'native-cases.cpp',HERE/'native-entry.S',Path(__file__),wine_signal,wine_unwind,fex_source/e.MODULE,fex_source/'FEXCore/Source/Interface/Core/Dispatcher/Dispatcher.cpp',fex_source/'FEXCore/include/FEXCore/Core/CoreState.h']}
 stamps={n:stat(n) for n in inputs};commands=[];runs=[];result={'status':'failed','scope':'real_arm64_fixture_and_extracted_bodies_not_production_FEX_or_device','inputHashes':inputs,'inputFingerprints':stamps,'commands':commands,'runs':runs}
 def command(name,argv,expected=0,marker=None):
  start=time.monotonic();log=output/(name+'.log')
  proc=subprocess.Popen([str(a) for a in argv],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
  try:data,_=proc.communicate(timeout=30)
  except subprocess.TimeoutExpired:
   os.killpg(proc.pid,signal.SIGKILL);data,_=proc.communicate();log.write_bytes(data)
   raise RuntimeError('native command timeout '+name)
  if len(data)>4*1024*1024:raise RuntimeError('native command output cap '+name)
  log.write_bytes(data)
  row={'name':name,'argv':[str(a) for a in argv],'exitCode':proc.returncode,'childReaped':proc.returncode is not None,'elapsedSeconds':time.monotonic()-start,'logSha256':sha(log)};commands.append(row)
  (output/(name+'.command.json')).write_text(json.dumps(row,indent=2)+'\n')
  if expected==0 and proc.returncode!=0:raise RuntimeError(name+' exit '+str(proc.returncode)+'; '+data.decode(errors='replace'))
  if expected=='assertion' and (proc.returncode!=-signal.SIGABRT or marker.encode() not in data):raise RuntimeError('missing intended negative assertion '+name)
  if marker and marker.encode() not in data:raise RuntimeError('missing marker '+name)
  return data.decode(errors='replace')
 flags=[CLANG,'-std=c++20','-O2','-Wall','-Wextra','-Wno-unused-parameter','-isysroot',SDK,'-I',HERE]
 try:
  asm=output/'entry.o';command('assembly',[CLANG,'-isysroot',SDK,'-c',HERE/'native-entry.S','-o',asm])
  tests=[('candidate',sources/'candidate.cpp',True,0,'PASS'),('non-ios',sources/'candidate.cpp',False,0,'PASS'),('original',sources/'original.cpp',True,'assertion','exact live EnterEC/native target snapshot has native LR')]
  source=(sources/'candidate.cpp').read_text()
  mutations=[('missing-native-membership','  if (!RtlIsEcCode(static_cast<ULONG_PTR>(IosJitReverseTranslate(GuestContext.Pc)))) {','  if (false) {','synthetic x64 target keeps original MM LR'),('missing-sp-match','Frame.IosEnterECSuspendSP != Context.X23 || ','','stale SP rejected, no alignment repair'),('missing-lr-match','Frame.IosEnterECSuspendLR != Context.Lr ||\n      ','','stale LR rejected'),('stale-mm-link','GuestContext.Lr = Frame.IosEnterECSuspendLR;','GuestContext.Lr = Frame.State.mm[0][0];','exact live EnterEC/native target snapshot has native LR')]
  for name,old,new,marker in mutations:
   if source.count(old)!=1:raise RuntimeError('mutation anchor mismatch '+name)
   mutated=source.replace(old,new)
   if name=='missing-sp-match':
    extra=' || GuestContext.Sp != Frame.IosEnterECSuspendSP'
    if mutated.count(extra)!=1:raise RuntimeError('second SP mutation anchor mismatch')
    mutated=mutated.replace(extra,'')
   path=sources/(name+'.cpp');path.write_text(mutated);tests.append((name,path,True,'assertion',marker))
  for name,path,ios,expected,marker in tests:
   obj=output/(name+'.o');exe=output/(name+'.exe');dep=output/(name+'.d')
   command(name+'-compile',flags+(['-DFEX_IOS_HOST'] if ios else [])+['-MD','-MF',dep,'-c',path,'-o',obj])
   command(name+'-link',[CLANG,'-isysroot',SDK,obj,asm,'-o',exe])
   text=command(name+'-run',[exe],expected,marker);runs.append({'name':name,'expected':expected,'output':text})
  for n,h in inputs.items():
   if sha(n)!=h or stat(n)!=stamps[n]:raise RuntimeError('source drift '+n)
  result['status']='native_candidate_non_ios_pass_original_and_four_mutants_rejected'
 except BaseException as err:
  result['error']=str(err);raise
 finally:
  result['outputHashes']={str(p.relative_to(output)):sha(p) for p in output.rglob('*') if p.is_file()}
  (output/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for name in ['output','fex-source','wine-signal','wine-unwind','compiler','sdk']: p.add_argument('--'+name,type=Path,required=True)
 args=p.parse_args();r=qualify(args.output,args.fex_source,args.wine_signal,args.wine_unwind,args.compiler,args.sdk)
 print(r['status']);print('reapedCommands='+str(len(r['commands'])))
