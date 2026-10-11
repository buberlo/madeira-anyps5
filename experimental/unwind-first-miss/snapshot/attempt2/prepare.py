"""Fresh output copies only; no Wine/compiler child is executed."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('attempt2_definitions',HERE/'run.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
ORIGINAL=HERE.parent/'unwind-first-miss-diagnostic-proposal/recipe.json'
ORIGINAL_SHA='b388e69384f8dc7c5917b5672fad934ff82ce6fa2b3c30a0884a69304138ffe4'
OLD_OUT=HERE.parent/'unwind-first-miss-diagnostic-build'
OLD_PREP=OLD_OUT/'preparation-receipt.json'
FAILED=OLD_OUT/'execution/receipt.json'
FAILED_SHA='ca1a0e6fc00b4ecc76220132fe88c06baae2c1d10ce42233a6c9946f8bc350de'


def derived_recipe(old):
    q=json.loads(json.dumps(old))
    q['output']=str(r.OUT);q['ownedPrefix']=str(r.OUT/'wine-prefix')
    for row in q['commands']:
        row['windowsArgv']=[value.replace(r.win(OLD_OUT),r.win(r.OUT)) for value in row['windowsArgv']]
        if 'cwd' in row:row['cwd']=row['cwd'].replace(str(OLD_OUT),str(r.OUT))
    q['attempt2History']={'originalRecipeSha256':ORIGINAL_SHA,
        'failedExecutionReceiptSha256':FAILED_SHA,'onlyCommandChanges':'exact_owned_output_path_substitution',
        'originalProviderMapUnchanged':True}
    return q


def check(review_sha):
    r.read(HERE/'source-review.json',review_sha)
    proof=json.loads((HERE/'source-review.json').read_text());r.replay(proof['inputs'])
    r.read(ORIGINAL,ORIGINAL_SHA);r.read(OLD_PREP,r.ORIGINAL_PREP_SHA);r.read(FAILED,FAILED_SHA)
    old=json.loads(ORIGINAL.read_text());prep=json.loads(OLD_PREP.read_text());failed=json.loads(FAILED.read_text())
    r.need(failed['status']=='failed' and failed['ownedPrefixJoined'] is True
        and failed['providersAndCopiesUnchanged'] is True, 'Exact closed failed attempt retained')
    r.read(r.RECIPE,r.RECIPE_SHA);q=json.loads(r.RECIPE.read_text())
    r.need(q==derived_recipe(old), 'Only exact owned path recipe substitution')
    r.need(prep['inputs']==old['inputs'] and len(prep['copies'])==14,'Exact original fourteen-copy map')
    r.replay(q['inputs']);r.replay(prep['copies'])
    return q,prep,proof


def prepare(review_sha):
    q,old,proof=check(review_sha)
    r.need(r.shutil.disk_usage(HERE).free>=r.MIN_FREE,'Initial2GiB copy reserve')
    r.need(not r.OUT.exists() and not r.OUT.is_symlink(),'Fresh attempt2 output')
    r.OUT.mkdir();copies={}
    for row in q['copies']:
        relative=Path(row['relativeTarget']);r.need(not relative.is_absolute() and '..' not in relative.parts,'Fixed copied path')
        source=OLD_OUT/relative;target=r.OUT/relative
        r.need(str(source) in old['copies'],'Exact independently re-read previous copied provider')
        r.read(source,old['copies'][str(source)]['sha256'],old['copies'][str(source)]['stableStat'])
        target.parent.mkdir(parents=True,exist_ok=True)
        with source.open('rb') as src,target.open('xb') as dst:
            for b in iter(lambda:src.read(r.MIB),b''):dst.write(b)
            dst.flush();os.fsync(dst.fileno())
        copies[str(target)]=r.read(target,q['inputs'][row['source']]['sha256'])
    r.replay(q['inputs']);r.replay(old['copies']);r.replay(proof['inputs']);r.replay(copies)
    data={'schema':1,'status':'diagnostic_source_and_runtime_copies_only_attempt2',
          'recipeSha256':r.RECIPE_SHA,'originalPreparationSha256':r.ORIGINAL_PREP_SHA,
          'sourceReviewSha256':review_sha,'failedExecutionReceiptSha256':FAILED_SHA,
          'inputs':q['inputs'],'copies':copies,'commandsExecuted':False,'runtimeQualified':False}
    with r.PREP.open('x') as f:
        json.dump(data,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
    return {'output':str(r.OUT),'preparationSha256':r.read(r.PREP)['sha256'],'commandsExecuted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--review-sha',required=True);p.add_argument('--prepare',action='store_true');a=p.parse_args()
    print(json.dumps(prepare(a.review_sha) if a.prepare else {'originalProviders':len(check(a.review_sha)[0]['inputs']),'commandsExecuted':False},sort_keys=True))
