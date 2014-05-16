#!/usr/bin/env python

# import multiprocessing

# def f(x):
# 	return x*x

# if __name__ == '__main__':
# 	count = multiprocessing.cpu_count()
# 	print "number of CPU's = %d" % count
# 	pool = multiprocessing.Pool(processes=10)              # start 4 worker processes
# 	result = pool.apply_async(f, [10])    # evaluate "f(10)" asynchronously
# 	print result.get(timeout=1)           # prints "100" unless your computer is *very* slow
# 	print pool.map(f, range(10))          # prints "[0, 1, 4,..., 81]"

import multiprocessing

def calculate(value):
    return value * 10

if __name__ == '__main__':
    pool = multiprocessing.Pool(None)
    tasks = range(100)
    results = []
    r = pool.map_async(calculate, tasks, callback=results.append)
    r.wait() # Wait on the results
    print results