import asyncio

class FakeChild:
 def __init__(self):self.pid=987654;self.returncode=None;self.event=asyncio.Event();self.stdout=self
 async def read(self,n):await self.event.wait();return b''
 async def wait(self):await self.event.wait();return self.returncode
 def kill(self):self.returncode=-9;self.event.set()

def kill_fake(child):
 def call(group,sig):
  if sig==0:
   if child.event.is_set():raise ProcessLookupError()
  elif child.returncode is None:child.kill()
  else:child.event.set()
 return call
