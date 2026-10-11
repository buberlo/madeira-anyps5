"""One own-element test, destination artifacts, and strict finite result parsing.

No device command or subprocess occurs on import. Compiling does not execute
the test, install the runner, qualify GPU rendering or satisfy the CPU gates.
"""
from pathlib import Path
import hashlib,importlib.util,json,plistlib,re,stat
HERE=Path(__file__).resolve().parent
OLD=HERE.with_name('native58-own-window-observation-proposal')
XCODE=Path('/Applications/Xcode.app/Contents/Developer/usr/bin/xcodebuild')
RESULT=Path('/Applications/Xcode.app/Contents/Developer/usr/bin/xcresulttool')
DEVICE='EXPLICIT_DEVICE_ID_REQUIRED'
BUNDLE='com.buberlo.anyps5ipad'
RUNNER='com.konradkern.anyps5ipad.ownstill.tests.xctrunner'
TEST='OwnWindowStillTests/testOwnForegroundStill'
TEST_MODULE='OwnWindowStillTests'
MAX_BUILD=200<<20;LIVE_BUILD=7086696039 # ceil(6.6 GiB)
MAX_CAPTURE=80<<20;MAX_IMAGE=20<<20;TIMEOUT=15

def need(v,m):
 if not v:raise ValueError(m)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def unique_json(blob):
 def pairs(rows):
  value={}
  for k,v in rows:need(k not in value,'Duplicate result JSON key');value[k]=v
  return value
 return json.loads(blob,object_pairs_hook=pairs)
def inherited():
 evidence=unique_json((HERE/'api-and-budget-evidence.json').read_bytes())
 for p,h in evidence['inputs'].items():need(sha(p)==h,'Exact local API/tool/held source changed')
 spec=importlib.util.spec_from_file_location('held_own_still',OLD/'proposal.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 return m
def context(wanted):
 keys={'schema','bundle','generation','ownedMainPID','observedBundlePath','manifestSha256','contextSha256'}
 need(type(wanted)is dict and set(wanted)==keys and wanted['schema']==1 and wanted['bundle']==BUNDLE,'Exact own still context')
 import uuid
 need(str(uuid.UUID(wanted['generation']))==wanted['generation'] and type(wanted['ownedMainPID'])is int and wanted['ownedMainPID']>0,'Current observer generation and decoded positive main PID')
 need(type(wanted['observedBundlePath'])is str and re.fullmatch('/private/var/containers/Bundle/Application/[A-F0-9-]{36}/Madeira[.]app',wanted['observedBundlePath']),'Actual own app path only')
 need(re.fullmatch('[0-9a-f]{64}',wanted['manifestSha256']) and sha_context(wanted)==wanted['contextSha256'],'Exact immutable host context digest')
 return wanted
def sha_context(wanted):return hashlib.sha256(canonical({k:v for k,v in wanted.items() if k!='contextSha256'})).hexdigest()
def xctestrun(wanted):
 context(wanted)
 target={'IsUITestBundle':True,'IsXCTRunnerHostedTestBundle':True,'UseDestinationArtifacts':True,
  'TestHostBundleIdentifier':RUNNER,'TestBundleDestinationRelativePath':'__TESTHOST__/PlugIns/OwnWindowStillTests.xctest',
  'UITargetAppBundleIdentifier':BUNDLE,'ProductModuleName':TEST_MODULE,'OnlyTestIdentifiers':[TEST],
  'EnvironmentVariables':{'ANYPS5_STILL_CONTEXT_JSON':canonical(wanted).decode()},'TestingEnvironmentVariables':{},
  'CommandLineArguments':[],'UITargetAppCommandLineArguments':[],'UITargetAppEnvironmentVariables':{},
  'ParallelizationEnabled':False,'SystemAttachmentLifetime':'keepNever','UserAttachmentLifetime':'keepAlways'}
 return {TEST_MODULE:target,'__xctestrun_metadata__':{'FormatVersion':1}}
def capture_commands(root,wanted):
 root=Path(root);context(wanted)
 return [[str(XCODE),'test-without-building','-xctestrun',str(root/'still.xctestrun'),
  '-destination','platform=iOS,id='+DEVICE,'-destination-timeout','5','-resultBundlePath',str(root/'still.xcresult'),
  '-only-testing:'+TEST_MODULE+'/'+TEST,'-parallel-testing-enabled','NO','-maximum-concurrent-test-device-destinations','1',
  '-test-timeouts-enabled','YES','-default-test-execution-time-allowance','8','-maximum-test-execution-time-allowance','8',
  '-test-iterations','1','-collect-test-diagnostics','never'],
  [str(RESULT),'get','test-results','summary','--schema-version','0.4.0','--path',str(root/'still.xcresult'),'--compact'],
  [str(RESULT),'export','attachments','--schema-version','0.4.0','--path',str(root/'still.xcresult'),
   '--output-path',str(root/'attachments')]]
def accepted_exports(summary,manifest,files,wanted):
 context(wanted)
 need(type(summary)is dict and summary.get('result')=='Passed' and
      all(type(summary.get(k))is int and summary[k]==v for k,v in
          {'totalTestCount':1,'passedTests':1,'failedTests':0,'skippedTests':0,'expectedFailures':0}.items()),'Exactly one passed own-element test')
 need(type(manifest)is list and len(manifest)==1 and manifest[0].get('testIdentifier') in (TEST,TEST+'()'), 'Exact one test attachment owner')
 rows=manifest[0].get('attachments');need(type(rows)is list and len(rows)==2,'Exactly own PNG and metadata attachments')
 names={};expected={'own-application-still.png','own-application-still.json'}
 for row in rows:
  label=row.get('suggestedHumanReadableName');name=row.get('exportedFileName')
  need(label in expected and label not in names and type(name)is str and name==Path(name).name and name not in ('','.', '..'), 'Closed two attachment names')
  need(row.get('isAssociatedWithFailure') is False and row.get('deviceId')==DEVICE and type(row.get('repetitionNumber',1))is int and row.get('repetitionNumber',1)==1,'Same physical device and single successful run')
  names[label]=name
 need(set(names)==expected and set(files)==set(names.values()),'Complete exact attachment file inventory')
 need(all(type(v)is bytes for v in files.values()),'Ordinary bounded exported attachment bytes')
 raw=files[names['own-application-still.json']];need(len(raw)<=64<<10,'Small still metadata')
 row=unique_json(raw);png=files[names['own-application-still.png']]
 inherited().accepted(row,png,wanted)
 return row,png
def build_command(root):
 root=Path(root)
 return [str(XCODE),'build-for-testing','-project',str(HERE/'OwnWindowStill.xcodeproj'),'-scheme','OwnWindowStill',
  '-configuration','Debug','-sdk','iphoneos','-destination','generic/platform=iOS','-derivedDataPath',str(root/'DerivedData'),
  '-clonedSourcePackagesDirPath',str(root/'SourcePackages'),'-disableAutomaticPackageResolution','-skipPackageUpdates','-jobs','1',
  'CODE_SIGNING_ALLOWED=NO','CODE_SIGNING_REQUIRED=NO','COMPILER_INDEX_STORE_ENABLE=NO','INDEX_ENABLE_DATA_STORE=NO',
  'SDK_STAT_CACHE_ENABLE=NO','CLANG_ENABLE_STAT_CACHE=NO','COMPILATION_CACHE_ENABLE_CACHING=NO',
  'SYMROOT='+str(root/'Products'),'OBJROOT='+str(root/'Intermediates'),'CACHE_ROOT='+str(root/'Caches'),
  'MODULE_CACHE_DIR='+str(root/'ModuleCache'),'CLANG_MODULE_CACHE_PATH='+str(root/'ModuleCache'),
  'SHARED_PRECOMPS_DIR='+str(root/'PrecompiledHeaders'),'SDK_STAT_CACHE_DIR='+str(root/'SDKStatCaches'),
  'OTHER_SWIFT_FLAGS=-module-cache-path '+str(root/'ModuleCache')]

# Exact local compiler tools; no build service or device entrypoint.
SWIFT=Path("/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/swiftc")
CLANG=Path("/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang")
