#!/usr/bin/env python3

from jobschedulers.jobscheduler_all import get_current_scheduler

import time
def print_timing(func):
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        print('%s took %0.3f ms' % (func.__name__, (t2-t1)*1000.0))
        return res
    return wrapper

@print_timing
def test():
    print('test')
    x = get_current_scheduler()
    jobs = x.get_current_running_job_ids()
    print(jobs)

@print_timing
def test2(js):
    jobs = js.get_running_job_ids()
    print(jobs)

def test3(js):
    jobs = js.get_waiting_job_ids()
    print(jobs)
    print(len(jobs))

def main():
    js = get_current_scheduler()
    test2(js)
    test2(js)
    test2(js)
    test3(js)
    test3(js)

if __name__ == "__main__":
    main()
