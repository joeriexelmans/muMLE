import os
import atexit

if "MUMLE_PROFILER" in os.environ:
    import time

    timings = {}

    class Timer:
        def __init__(self, text):
            self.text = text
        def __enter__(self):
            self.start_time = time.perf_counter_ns()
        def __exit__(self, exc_type, exc_value, traceback):
            self.end_time = time.perf_counter_ns()
            duration = self.end_time - self.start_time
            existing_timing, count = timings.get(self.text, (0, 0))
            timings[self.text] = (existing_timing + duration, count+1)

    def __print_timings():
        if len(timings)>0:
            print(f'Timings:')
            tuples = [(text,(duration,count)) for text, (duration, count) in timings.items()]
            tuples.sort(key=lambda tup: -tup[1][0])
            for text, (duration, count) in tuples:
                print(f'  {text}  {round(duration/1000000)} ms ({count} times, {round(duration/count/1000000)} ms avg.)')

    atexit.register(__print_timings)

else:
    class Timer:
        def __init__(self, text):
            pass
        def __enter__(self):
            pass
        def __exit__(self, exc_type, exc_value, traceback):
            pass





def counted(f):
    def wrapped(*args, **kwargs):
        wrapped.calls += 1
        return f(*args, **kwargs)
    wrapped.calls = 0
    def ccc():
        print(f'{f} was called {wrapped.calls} times')
    atexit.register(ccc)
    return wrapped