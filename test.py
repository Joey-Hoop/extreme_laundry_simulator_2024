import multiprocessing
import multiprocessing.pool
import multiprocessing.process
from multiprocessing import Process
import time
from math import ceil

# THIS FILE IS AN EXAMPLE!!
# This file does not affect the running program or gui in any way
CPU_COUNT = multiprocessing.cpu_count()

def example(min: int, max: int):
    theRange = max - min
    for i in range(theRange):
        print(i + min, end = " ")
        if(i % 20 == 0):
            time.sleep(1)

def example2():
    print("Hello from a process")

# In Parallel
if __name__ == '__main__':
    # CPU_COUNT = multiprocessing.cpu_count()
    print("CPU count: " + str(CPU_COUNT))
    print("Enter Min: ")
    min = int(input())
    print("Enter Max: ")
    max = int(input())

    step_size = ceil((max - min) / CPU_COUNT)
    print("In Parallel:")

    processes = []
    for i in range(CPU_COUNT):
        process_min = (i * step_size) + min
        process_max = process_min + step_size if (process_min + step_size < max) else max
        processes.append(Process(target=example, args=(process_min, process_max)))

    start = time.clock_gettime(time.CLOCK_REALTIME)

    for p in processes:
        p.start()
    for p in processes:
        p.join()
    stop = time.clock_gettime(time.CLOCK_REALTIME)

    print('Time: ', stop - start)  
    # In Sequence:
    print("\nIn Sequence:")
    start = time.clock_gettime(time.CLOCK_REALTIME)
    example(min, max)
    stop = time.clock_gettime(time.CLOCK_REALTIME)
    print('Time: ', stop - start)  
