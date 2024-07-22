import multiprocessing
import multiprocessing.pool
import multiprocessing.process
from multiprocessing import Process, current_process, Manager
from multiprocessing import Lock
import multiprocessing.shared_memory
import time
from math import ceil
import ctypes
import json
import csv
# THIS FILE IS AN EXAMPLE!!
# This file does not affect the running program or gui in any way
CPU_COUNT = multiprocessing.cpu_count() - 1
'''
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
'''

def example(min: int, max: int, array):
    '''for i in range(min, max, 1):
        lock.acquire()
        try:
            array.append(i)
        finally:
            lock.release()
    '''
    if current_process().name == "Process-1":
        print("I am main")
    array.append(str(current_process()))

def exampleTwo(lock, barrier):
    
    if int(current_process().name[8:]) % CPU_COUNT == 0:
        time.sleep(2)
        print("I am main, I am: " + str(current_process().name))
        with lock:
            with open("test.csv", 'a', newline='', encoding='utf-8') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(["I am main, I am: " + str(current_process().name)])

    barrier.wait()
    print(str(current_process().name[8:]))
    with lock:
        with open("test.csv", 'a', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            
            csv_writer.writerow([str(current_process().name)])

# In Parallel

if __name__ == '__main__':
    
    print("CPU count: " + str(CPU_COUNT))
    print(current_process())
    barrier = multiprocessing.Barrier(CPU_COUNT)
    #print("Enter Min: ")
    #min = int(input())
    #print("Enter Max: ")
    #max = int(input())
    #array = multiprocessing.Manager().list()
    #array = multiprocessing.Array(ctypes.c_wchar_p, [])
    lock = Lock()
    #step_size = ceil((max - min) / CPU_COUNT)

    print("In Parallel:")
    def testBoy():
        processes = []
        for i in range(CPU_COUNT):
            #process_min = (i * step_size) + min if ((i * step_size) + min < max) else max
            #process_max = process_min + step_size if (process_min + step_size < max) else max
            processes.append(Process(target=exampleTwo, args=(lock, barrier)))

        for p in processes:
            p.start()
        for p in processes:
            p.join()
    testBoy()
    testBoy()
    testBoy()
    testBoy()
