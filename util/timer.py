import os

if "MUMLE_PROFILER" in os.environ:
    import time
    import atexit

    timings = {}

    class Timer:
        def __init__(self, text):
            self.text = text
        def __enter__(self):
            self.start_time = time.perf_counter_ns()
        def __exit__(self, exc_type, exc_value, traceback):
            self.end_time = time.perf_counter_ns()
            duration = self.end_time - self.start_time
            existing_timing = timings.get(self.text, 0)
            timings[self.text] = existing_timing + duration

    def __print_timings():
        if len(timings)>0:
            print(f'Timings:')
            tuples = [(text,duration) for text, duration in timings.items()]
            tuples.sort(key=lambda tup: -tup[1])
            for text, duration in tuples:
                print(f'  {text}  {round(duration/1000000)} ms')

    atexit.register(__print_timings)

else:
    class Timer:
        def __init__(self, text):
            pass
        def __enter__(self):
            pass
        def __exit__(self, exc_type, exc_value, traceback):
            pass
