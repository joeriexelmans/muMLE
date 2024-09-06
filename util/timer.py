import time

class Timer:
    def __init__(self, text):
        self.text = text
    def __enter__(self):
        self.start_time = time.perf_counter_ns()
    def __exit__(self, exc_type, exc_value, traceback):
        self.end_time = time.perf_counter_ns()
        print(self.text, (self.end_time - self.start_time)/1000000, "ms")
