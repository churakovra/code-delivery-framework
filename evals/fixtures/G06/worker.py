async def run(resource, wait):
    await wait()
    await resource.close()
