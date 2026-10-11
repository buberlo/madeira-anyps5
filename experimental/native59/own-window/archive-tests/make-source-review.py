#!/usr/bin/env python3
"""Only source/API readback and tiny pure controls; no compiler or runner calls."""
from pathlib import Path
import datetime,json,os,stat,subprocess,sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import protocol as p,direct_build as d
def overlay_inputs(evidence):
 delta=evidence['xctestOverlayDelta'];base=d.PLATFORM/'usr/lib/XCTest.swiftmodule'
 names={str(base/n) for n in ('arm64-apple-ios.swiftinterface','arm64-apple-ios.swiftdoc')}
 p.need(delta['target']==d.TARGET and delta['compileOnlyAddedArguments']==['-I',str(base.parent)],'Exact ARM64 XCTest compile overlay route')
 p.need(set(delta['providers'])==names,'Only actual ARM64 XCTest interface and doc')
 for name,row in delta['providers'].items():
  path=Path(name);before=identity(name)
  p.need(path==path.resolve() and not any(x.is_symlink() for x in [path,*path.parents]) and
         stat.S_ISREG(path.lstat().st_mode) and path.stat().st_nlink==1,'Ordinary exact XCTest overlay input')
  p.need(set(row)=={'sha256','bytes','stat'} and before['stat']==row['stat'] and row['bytes']==path.stat().st_size,
         'Declared overlay byte count and seven-field identity')
  p.need(evidence['inputs'].get(name)==row['sha256'] and p.sha(path)==row['sha256'],'Complete exact overlay provider bytes')
  p.need(identity(name)==before,'Overlay identity stable through SHA replay')
 interface=(base/'arm64-apple-ios.swiftinterface').read_text()
 p.need('-target '+d.TARGET in interface and '-module-name XCTest' in interface,'Actual target interface declaration')
 p.need(all('public func '+name in interface for name in ('XCTUnwrap','XCTAssertNotNil','XCTAssertFalse','XCTAssertEqual','XCTAssertGreaterThan','XCTAssertLessThanOrEqual')),'Original assertion APIs are supplied by Swift overlay')
 return {name:row['sha256'] for name,row in delta['providers'].items()}
def identity(name):
 x=Path(name);s=x.stat();l=x.lstat();p.need(stat.S_ISREG(s.st_mode),'Declared regular source/API/tool')
 return {'literalPath':str(x),'resolvedPath':str(x.resolve()),
  'stat':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_mode,s.st_nlink],
  'literalStat':[l.st_dev,l.st_ino,l.st_size,l.st_mtime_ns,l.st_ctime_ns,l.st_mode,l.st_nlink]}
def write(name,raw):
 p.need(len(raw)<=2<<20,'Small source proof cap')
 with (p.HERE/name).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
def main():
 p.need(sys.argv[1:]==['--source-review'],'Explicit source-only mode')
 p.need(not any((p.HERE/n).exists() for n in ('controls.log','offline-receipt.json','source-review-freeze.json')),'Exclusive source outputs')
 evidence=p.unique_json((p.HERE/'api-and-budget-evidence.json').read_bytes());inputs=dict(evidence['inputs'])
 own=('protocol.py','bounded_child.py','compiler_locks.py','local_build.py','direct_build.py','capture.py','test_runner.py','test_direct.py','test_diagnostic.py','test_compiler_locks.py','README.md',
  'installed-compiler-lock-evidence.json','source-delta-inspection.json','source-delta.patch','swift-modulecache-source-evidence.json','test_swift_modulecache.py',
  'make-source-review.py','api-and-budget-evidence.json','test_xctest_overlay.py','OwnWindowStillTests/OwnWindowStillTests.swift',
  'OwnWindowStill.xcodeproj/project.pbxproj','OwnWindowStill.xcodeproj/xcshareddata/xcschemes/OwnWindowStill.xcscheme')
 for name in own:inputs[str(p.HERE/name)]=p.sha(p.HERE/name)
 before={n:identity(n) for n in inputs};p.inherited();overlay_inputs(evidence)
 p.need(d.runtime_map()==evidence['runtimeProviders'],'Actual exact SDK runtime tree')
 args=[sys.executable,'-I','-B','-m','unittest','discover','-s',str(p.HERE),'-p','test_*.py']
 run=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
 p.need(len(run.stdout)<=1<<20,'Bounded controls log');write('controls.log',run.stdout)
 p.need(run.returncode==0 and b'Ran 115 tests' in run.stdout and b'\nOK\n' in run.stdout,'All109 inherited controls plus6 narrow overlay controls')
 after={n:identity(n) for n in inputs};overlay_inputs(evidence);p.need(before==after and all(p.sha(n)==h for n,h in inputs.items()),'Source/API/runtime bytes and identities retained')
 value={'schema':1,'status':'source_only_direct_swift_arm64_xctest_overlay_controls_passed_not_built_or_device_ready',
  'createdUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'caseCount':115,'inheritedCaseCount':109,'intentionallyAdaptedInheritedExpectations':2,'newCaseCount':6,'exitCode':0,'failures':0,'errors':0,'skipped':0,
  'command':args,'inputs':inputs,'inputFingerprints':before,'finalInputFingerprints':after,'controlsLogSha256':p.sha(p.HERE/'controls.log'),
  'compilerActions':False,'deviceActions':False,'actualScreenshotsCaptured':False,'runnerCompiled':False,'runnerSigned':False,
  'realRunnerLifecycleAdapterImplemented':False,'captureReady':False,'buildBudgetBytes':p.MAX_BUILD,'liveBuildReserveBytes':p.LIVE_BUILD}
 write('offline-receipt.json',p.canonical(value)+b'\n')
 inputs.update({str(p.HERE/n):p.sha(p.HERE/n) for n in ('controls.log','offline-receipt.json')});final={n:identity(n) for n in inputs}
 frozen={'schema':1,'status':'held_direct_swift_arm64_xctest_overlay_local_build_recipe_not_runtime_ready','inputs':inputs,
  'runtimeProviders':evidence['runtimeProviders'],'inputFingerprints':final,'finalInputFingerprints':final,
  'offlineReceiptSha256':p.sha(p.HERE/'offline-receipt.json'),'caseCount':115,'compilerActions':False,'deviceActions':False,'captureReady':False}
 write('source-review-freeze.json',p.canonical(frozen)+b'\n')
 print(json.dumps({'sourceReviewSha256':p.sha(p.HERE/'source-review-freeze.json'),'offlineReceiptSha256':frozen['offlineReceiptSha256'],'caseCount':115,'inputs':len(inputs)}))
if __name__=='__main__':main()
