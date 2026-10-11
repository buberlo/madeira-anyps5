"""Bounded test-without-building and xcresult adapter, no live CLI.

Root integration must supply an actual compiled/signed/installed runner reader
and its exact runner-process/service close operation. No such runtime tuple is
represented by the unsigned local build. The inherited launcher retains all
Native58/CPU/import/lease/observer/main-PID gates around this call.
"""
from pathlib import Path
import asyncio,os,plistlib,time
import protocol as p,bounded_child as b

class Capture:
 def __init__(self,quota,guard,runner_lifecycle):
  p.need(runner_lifecycle is not None,'Actual signed installed runner identity/closure adapter required')
  self.quota=quota;self.guard=guard;self.lifecycle=runner_lifecycle;self.commands=[]
 async def __call__(self,wanted):
  p.context(wanted);self.guard()
  # This mandatory reader must prove products/signature/current runner identity
  # plus matching output root/generation, before any test child/output creation.
  await self.lifecycle.before(wanted,self.quota.root)
  p.need(self.quota.used+p.MAX_CAPTURE+p.MAX_IMAGE+(64<<10)<=self.quota.limit,'Capture and final PNG metadata within shared128 MiB quota')
  root=b.unlinked_parent(Path(self.quota.root)/('own-still-'+wanted['generation']))
  p.need(not root.exists(),'One exclusive capture; no retry');root.mkdir()
  deadline=time.monotonic()+p.TIMEOUT;failure=None;result=None
  def guard():
   self.guard();b.inventory(root,p.MAX_CAPTURE)
   # Account all result/exports/logs, not just the PNG returned to the hook.
   b.inventory(self.quota.root,self.quota.limit)
  try:
   raw=plistlib.dumps(p.xctestrun(wanted),fmt=plistlib.FMT_XML,sort_keys=True)
   with (root/'still.xctestrun').open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
   for i,argv in enumerate(p.capture_commands(root,wanted)):
    row=await b.command(argv,root,guard,deadline,p.MAX_CAPTURE,label='xctest' if i==0 else 'result-'+str(i))
    self.commands.append(row)
   summary=p.unique_json((root/'result-1.log').read_bytes())
   export=root/'attachments';rows,unused,unused2=b.inventory(export,(p.MAX_IMAGE+(64<<10)))
   p.need('manifest.json' in rows and len(rows)==3,'Only two exported attachments plus SDK manifest')
   manifest=p.unique_json((export/'manifest.json').read_bytes())
   files={n:(export/n).read_bytes() for n in rows if n!='manifest.json'}
   result=p.accepted_exports(summary,manifest,files,wanted);guard()
  except BaseException as e:failure=e
  finally:
   # Child cancellation/drain completes in command(). Native test services are
   # a separate required lifecycle proof, not inferred from host exit zero.
   task=asyncio.create_task(self.lifecycle.close(wanted,self.commands))
   try:await asyncio.wait_for(asyncio.shield(task),3)
   except BaseException as e:
    if not task.done():task.cancel()
    await asyncio.gather(task,return_exceptions=True)
    if failure is None:failure=e
  if failure is not None:raise failure
  self.guard();return result
