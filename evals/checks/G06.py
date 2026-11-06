import asyncio, worker
async def test():
    class Resource:
        closed=False
        async def close(self): self.closed=True
    resource=Resource(); started=asyncio.Event()
    async def wait():
        started.set(); await asyncio.Event().wait()
    task=asyncio.create_task(worker.run(resource, wait)); await started.wait(); task.cancel()
    try: await task
    except asyncio.CancelledError: pass
    assert resource.closed
asyncio.run(test())
