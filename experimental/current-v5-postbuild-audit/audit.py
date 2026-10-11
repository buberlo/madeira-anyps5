"""Read completed local V5 artifacts only; never build, patch or launch runtime."""
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile
HERE=Path(__file__).resolve().parent
FULL=HERE.parent
ROOT=FULL.parents[1]
BUILD=FULL/'winlibs-build-v5'
SOURCE=FULL/'qualification-source-v5'
ARCHIVE=FULL/'hle-v5/hle-runtime.zip'
PROVENANCE=ARCHIVE.with_suffix('.provenance.json')
PREPARATION=FULL/'qualification-source-v5-preparation.json'
PRIVATE='APS5NativeCompilerOnce_nid_no_patch'
HELPERS={'pthread_once','__imp_pthread_once','APS5CompilerOnceBridge','APS5CompilerOnceResolvedTarget'}

def need(value,message):
    if not value:raise ValueError(message)

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def read(path,maximum=64*1024**2):
    p=Path(path);a=p.lstat()
    stamp=lambda s:[s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
    need(stat.S_ISREG(a.st_mode) and a.st_nlink==1 and a.st_size<=maximum,'Bounded ordinary artifact: '+str(p))
    data=p.read_bytes();need(stamp(a)==stamp(p.lstat()),'Artifact changed during read: '+str(p))
    return data,hashlib.sha256(data).hexdigest()

def review_replay():
    review=json.loads(read(HERE/'source-review.json')[0])
    need(review.get('status')=='source_only_v5_postbuild_audit_not_executed','Held audit source status')
    for name,digest in review['inputs'].items():
        need(read(ROOT/name)[1]==digest,'Held audit source/baseline drift: '+name)

def source_replay(preparation):
    need(preparation['upstreamCommit']=='a11c8f7f70a0ed4e71504a89de69e8cdae687817'
         and preparation['source']==str(SOURCE) and len(preparation['sourceFiles'])==2136,'Exact prepared V5 source')
    for name,digest in preparation['sourceFiles'].items():
        need(read(SOURCE/name)[1]==digest,'V5 source content drift: '+name)

def coverage(manifest,provenance,preparation,helper,additional_log):
    need(manifest.get('schema')==1 and manifest.get('kind')=='anyps5_unpatched_hle_runtime'
         and manifest.get('source_commit')==preparation['upstreamCommit']
         and manifest.get('contains_game_data') is False and manifest.get('runtime_verified') is False,
         'Honest actual unpatched HLE manifest')
    need(manifest['build_provenance']==provenance,'Embedded/external actual provenance equality')
    p=provenance
    need(p['targets']==preparation['selectedPrxTargets'] and len(p['targets'])==47,
         'Exact selected47 modules')
    need(p['host_tests_passed']==list(helper.TESTS)==preparation['requiredDefaultHostTestTargets']
         and len(helper.TESTS)==42,'All42 required default targets')
    need(p['additional_host_tests_passed']==preparation['additionalTestTargets']
         and len(p['additional_host_tests_passed'])==6,'All six selected additional targets')
    inventory=helper.additional_ctest_inventory(p['additional_host_tests_passed'],additional_log)
    need(inventory.get('windows_compiler_once')=='compiler_once_tests','Real registered once fixture arguments/case')
    once_registration(additional_log)
    expected=set(inventory)
    for names,_ in helper.CTEST_CONTRACTS.values():expected.update(names)
    need(set(p['host_test_case_results'])==expected
         and all(row.get('status')=='passed' for row in p['host_test_case_results'].values())
         and p['host_test_cases_skipped']==[],'Every selected registered case passed without skip')
    need(p['host_test_runtime_inputs_verified_unchanged'] is True
         and p['device_or_gameplay_verified'] is False
         and p['anyps5_commit']==preparation['upstreamCommit'],'Actual local CPU provenance limits')
    patches={q.name:read(q)[1] for q in (ROOT/'patches/anyps5').glob('*.patch')}
    need(len(patches)==12 and p['patches']==patches,'Exact promoted V5 twelve-patch provenance')
    return inventory

def once_registration(text):
    tests=[t for t in json.loads(text)['tests'] if t.get('name')=='windows_compiler_once']
    expected=[BUILD/'tests/compiler_once_tests.exe',BUILD/'core/libs/libs/unpatched/libc.prx',BUILD/'tests/compiler_once_cross.dll']
    need(len(tests)==1 and tests[0].get('command')==['Z:'+str(p) for p in expected],
         'Actual focused registration must pass exact libc and cross-module paths')

def link_blocks(text):
    lines=text.splitlines();result={}
    for index,line in enumerate(lines):
        if not line.startswith('build ') or ': CXX_' not in line or '_LINKER__' not in line:continue
        outputs,tail=line[6:].split(': ',1);tokens=tail.split();objects=[]
        for token in tokens[1:]:
            if token in ('|','||'):break
            objects.append(token)
        values={}
        j=index+1
        while j<len(lines) and lines[j].startswith('  '):
            key,separator,value=lines[j].strip().partition(' = ')
            if separator:values[key]=value
            j+=1
        for output in outputs.split():
            need(output not in result,'Duplicate actual link output')
            result[output]={'objects':objects,'header':line,'values':values}
    return result

def route_imports(imports,libc_linked,is_libc=False):
    normalized={name.lower():symbols for name,symbols in imports.items()}
    need(len(normalized)==len(imports),'Case-aliased imported library')
    if libc_linked:
        need(not any('pthread_once' in values for values in normalized.values()),'Owned image still imports native pthread_once')
        if not is_libc:need(PRIVATE in normalized.get('libc.prx',[]),'Owned caller private libc provider import absent')

def exports(recipe,image):
    # EXE images may legitimately have no export directory.
    if image.directory(0)==(0,0):return {}
    return recipe.export_contract(image)

def libc_linked(block,is_libc=False):
    return is_libc or 'core/libs/libs/implib/liblibc.dll.a' in (
        block['header']+' '+block['values'].get('LINK_LIBRARIES',''))

def bridge_sources(graph_text,objects,is_libc=False):
    for name in objects:
        rows=[line for line in graph_text.splitlines() if line.startswith('build '+name+': CXX_COMPILER__')]
        expected='Z$:'+str(SOURCE/'core/libs/prx/libc/src/specifics/windows/caller_bridge.cpp')
        need(len(rows)==1 and rows[0].split()[3]==expected,'Bridge must compile the exact prepared current source')

def focused_output(xml_text,registered,recipe):
    cases=ET.fromstring(xml_text).findall('.//testcase')
    need([c.get('name') for c in cases].count('windows_compiler_once')==1,'One actual focused CTest result')
    case=next(c for c in cases if c.get('name')=='windows_compiler_once')
    need(case.get('status','run')=='run' and not any(case.find(t) is not None for t in ('failure','error','skipped')),
         'Focused CTest really passed')
    need(registered.get('windows_compiler_once')=='compiler_once_tests','Registered focused executable identity')
    text='\n'.join(node.text or '' for node in case.findall('system-out'))
    rows=[line.removeprefix('COMPILER_ONCE_PASS ') for line in text.splitlines() if line.startswith('COMPILER_ONCE_PASS ')]
    need(rows==list(recipe.CASES) and text.splitlines().count('COMPILER_ONCE_COMPLETE cases=8 errors=0')==1
         and 'COMPILER_ONCE_FAILED' not in text,'Eight ordered actual focused markers and one completion')
    return text

def export_baseline(actual,baseline,is_libc):
    actual=dict(actual)
    if is_libc:need(actual.pop(PRIVATE,None)=={'ordinal':1062,'data':False},'Private1062 code export')
    need(actual==baseline,'Existing module export names/ordinals/DATA changed')
    need(not HELPERS.intersection(actual),'Incidental bridge exports escaped')

def frame_section(image):
    data=image.data;header=struct.unpack_from('<I',data,0x3c)[0]
    count=struct.unpack_from('<H',data,header+6)[0]
    offset=header+24+struct.unpack_from('<H',data,header+20)[0]
    names={data[offset+40*i:offset+40*i+8].rstrip(b'\0') for i in range(count)}
    need(b'.ehfram' in names and b'.eh_fram' not in names,'Owned custom-unwinder frame section')

def audit():
    # A real completed archive and its producer provenance are required before
    # touching any incomplete compiler output. No synthetic HLE can be emitted.
    archive_bytes,archive_sha=read(ARCHIVE,128*1024**2)
    provenance_bytes,provenance_sha=read(PROVENANCE,16*1024**2)
    review_replay()
    preparation=json.loads(read(PREPARATION)[0]);source_replay(preparation)
    helper=load(ROOT/'scripts/build-hle.py','current_hle')
    recipe=load(FULL/'windows-compiler-once-direct-provider-proposal/recipe.py','direct_candidate')
    provenance=json.loads(provenance_bytes)
    additional_text=read(BUILD/'inventory-additional.log',16*1024**2)[0].decode()
    with zipfile.ZipFile(ARCHIVE) as z:
        rows=z.infolist();need(len(rows)==51 and len({r.filename for r in rows})==51,'Exact51 HLE ZIP members')
        need(all(not r.is_dir() and not r.flag_bits&1 and stat.S_IFMT(r.external_attr>>16) in (0,stat.S_IFREG)
             and r.file_size<=64*1024**2 for r in rows),'Ordinary bounded HLE members')
        need(sum(r.file_size for r in rows)<=128*1024**2,'HLE uncompressed aggregate bound')
        manifest=json.loads(z.read('hle-manifest.json'))
        registered=coverage(manifest,provenance,preparation,helper,additional_text)
        expected={'unpatched/'+n+'.prx' for n in preparation['selectedPrxTargets']}|{
            'runtime/'+n for n in ('libgcc_s_seh-1.dll','libstdc++-6.dll','libwinpthread-1.dll')}
        need(set(manifest['files'])==expected and set(z.namelist())==expected|{'hle-manifest.json'},'Raw47/runtime3 exact inventory')
        for name,digest in manifest['files'].items():
            need(hashlib.sha256(z.read(name)).hexdigest()==digest,'Archive member hash differs: '+name)
            disk=BUILD/'core/libs/libs/unpatched'/Path(name).name if name.startswith('unpatched/') else ROOT/'build/toolchains/winlibs/mingw64/bin'/Path(name).name
            need(read(disk)[1]==digest,'Archive/current built provider differs: '+name)
    graph_text=read(BUILD/'build.ninja',16*1024**2)[0].decode()
    graph=link_blocks(graph_text)
    binaries=[('core/libs/libs/unpatched/'+name+'.prx',True,name=='libc') for name in preparation['selectedPrxTargets']]
    binaries += [('tests/'+name+'.exe',False,False) for name in list(helper.TESTS)+preparation['additionalTestTargets']]
    binaries += [('tests/compiler_once_cross.dll',False,False)]
    evidence={};linked=0
    for name,module,is_libc in binaries:
        need(name in graph,'Missing actual final link rule: '+name)
        block=graph[name];bridge=[o for o in block['objects'] if o.endswith('/caller_bridge.cpp.obj')]
        owns_once=libc_linked(block,is_libc)
        if owns_once:
            linked+=1;need(len(bridge)==1,'Exactly one owned bridge per final image: '+name)
            symbols=recipe.coff_symbols(BUILD/bridge[0])
            need(all(symbols.get(n,{}).get('section',0)>0 for n in ('pthread_once','__imp_pthread_once')),'Both direct and IAT bridge definitions')
            bridge_sources(graph_text,bridge,is_libc)
        image=recipe.pe(BUILD/name);route_imports(image.imports(),owns_once,is_libc)
        contract=exports(recipe,image)
        need(not HELPERS.intersection(contract) and (is_libc or PRIVATE not in contract),'Private/helper autoexports escaped: '+name)
        if module:
            baseline=exports(recipe,recipe.pe(recipe.BUILD/name))
            export_baseline(contract,baseline,is_libc)
        if owns_once:frame_section(image)
        if str(BUILD/name).removeprefix(str(ROOT)+'/') in provenance['host_test_runtime_inputs']:
            need(read(BUILD/name)[1]==provenance['host_test_runtime_inputs'][str(BUILD/name).removeprefix(str(ROOT)+'/')],'Final runtime fixture differs from tested hash')
        else:raise ValueError('Final image absent from producer tested runtime closure: '+name)
        evidence[name]={'sha256':read(BUILD/name)[1],'libcLinked':owns_once,'bridgeObjects':bridge,'namedExportCount':len(contract)}
    # Inspect marker logs directly; receipt-level booleans alone are insufficient.
    original=read(BUILD/'test-windows_exception_tests.log',2*1024**2)[0].decode()
    need(original.splitlines().count(recipe.ORIGINAL_MARKER)==1,'Original complete WindowsExceptions marker')
    focused=read(BUILD/'test-additional.xml',2*1024**2)[0].decode()
    focused_output(focused,registered,recipe)
    case_rows=helper.additional_ctest_results(registered,BUILD/'test-additional.xml')
    need(all(provenance['host_test_case_results'][name]==value for name,value in case_rows.items()),
         'Actual additional JUnit matches producer results')
    source_replay(preparation)
    review_replay()
    need(read(ARCHIVE,128*1024**2)[1]==archive_sha and read(PROVENANCE,16*1024**2)[1]==provenance_sha,'Final archive/provenance stable')
    return {'schema':1,'status':'read_only_actual_v5_hle_static_and_cpu_provenance_verified_not_gpu_or_game',
        'archiveSha256':archive_sha,'provenanceSha256':provenance_sha,'sourceFilesVerified':len(preparation['sourceFiles']),
        'selectedModules':47,'requiredDefaultTargets':42,'selectedAdditionalTargets':6,'registeredAdditionalCases':registered,
        'inspectedImages':len(evidence),'libcLinkedOwnedImages':linked,'images':evidence,
        'originalWindowsExceptionsMarkerVerified':True,'rawPrivateNoPatchNameAndOrdinalVerified':True,
        'nidPatchedPrivateNameNotYetMaterialized':True,'nativeDllInternalOnceIatsQualified':False,
        'gpuVerified':False,'gameplayVerified':False,'deviceExecuted':False}

if __name__=='__main__':
    need(sys.argv[1:]==['--read-only'],'Only explicit read-only audit mode')
    print(json.dumps(audit(),sort_keys=True,indent=2))
