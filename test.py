import multiprocessing
import multiprocessing.pool
import multiprocessing.process
from multiprocessing import Process, current_process
from multiprocessing import Lock
import time
from math import ceil
import json
import csv
# THIS FILE IS AN EXAMPLE!!
# This file does not affect the running program or gui in any way
if __name__ == '__main__':
    CPU_COUNT = multiprocessing.cpu_count() - 1

    # For headers list:
    with open("configs.json", "r") as json_file:
        configs = json.load(json_file)
    headers = []
    for header in configs:
        if configs[header]:
            headers.append(header)


    row = ["Dumb " + header for header in configs]
    print("Before filter:\n" + str(row))
    row[:] = [column for config, column in zip(configs, row) if configs[config]]
    print("After filter:\n" + str(row))

    print(CPU_COUNT)
#somelist[:] = [tup for tup in somelist if determine(tup)]
#For labels, just dont append them until after row is defined the first time. Do the loop above, then include a seperate final if statement that adds
#the labels if configs['labels'] is true. In general we should move labels to the end.


def example(min: int, max: int, lock):
    theRange = max - min
    for i in range(theRange):
        lock.acquire()
        try:
            print(i + min, end = " ")
        finally:
            lock.release()
        if(i % 20 == 0):
            time.sleep(1)

def exampleTwo(lock):
    print(current_process())
    if current_process().name == "Process-1":
        print("I am main")
    with open("test.csv", 'a', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        with lock:
            csv_writer.writerow([str(current_process().name)])

# In Parallel

if __name__ == '__main__':
    # CPU_COUNT = multiprocessing.cpu_count()
    print("CPU count: " + str(CPU_COUNT))
    
    print("Enter Min: ")
    min = int(input())
    print("Enter Max: ")
    max = int(input())

    lock = Lock()
    step_size = ceil((max - min) / CPU_COUNT)

    print("In Parallel:")

    processes = []
    for i in range(CPU_COUNT):
        process_min = (i * step_size) + min
        process_max = process_min + step_size if (process_min + step_size < max) else max
        processes.append(Process(target=exampleTwo, args=(lock,)))

    for p in processes:
        p.start()
    for p in processes:
        p.join()

'''
    print('Time: ', stop - start)  
    # In Sequence:
    print("\nIn Sequence:")
    start = time.clock_gettime(time.CLOCK_REALTIME)
    example(min, max, lock)
    stop = time.clock_gettime(time.CLOCK_REALTIME)
    print('Time: ', stop - start)  
'''