import multiprocessing
import multiprocessing.pool
import multiprocessing.process
from multiprocessing import Process
import time

# THIS FILE IS AN EXAMPLE!!
# This file does not affect the running program or gui in any way

def example(min: int, max: int):
    theRange = max - min
    for i in range(theRange):
        print(i + min, end = " ")
        if(i % 20 == 0):
            time.sleep(1)
    print("\nDone!")

def example2():
    print("Hello from a process")

# In Parallel
if __name__ == '__main__':
    CPU_COUNT = multiprocessing.cpu_count()
    print("CPU count: " + str(CPU_COUNT))
    # start = time.clock_gettime(time.CLOCK_REALTIME)
    processes = []
    for i in range(CPU_COUNT):
        processes.append(Process(target=example, args=(i * 100,(i*100)+100)))
    start = time.clock_gettime(time.CLOCK_REALTIME)
    for p in processes:
        p.start()
    for p in processes:
        p.join()
    stop = time.clock_gettime(time.CLOCK_REALTIME)
    print('Time: ', stop - start)  



'''
# In Sequence:

start = time.clock_gettime(time.CLOCK_REALTIME)
example(0,400)
stop = time.clock_gettime(time.CLOCK_REALTIME)
print('Time: ', stop - start)  
'''