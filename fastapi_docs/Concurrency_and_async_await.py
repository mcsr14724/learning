import asyncio
import time

async def work_1():
    print("Starting work 1")
    await asyncio.sleep(5)
    print("Finished work 1")

async def work_2():
    print("Starting work 2")
    await asyncio.sleep(5)
    print("Finished work 2")

async def main():
    start = time.time()
    await asyncio.gather(work_1(),work_2())
    end = time.time()
    print(f"Total time taken: {end - start:.2f} seconds")

asyncio.run(main())