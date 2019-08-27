import time

from train_runner.kernel import Project, Kernel, KERNEL_STATUS_UNKNOWN, KERNEL_STATUS_CANCELED, KERNEL_STATUS_COMPLETE, KERNEL_STATUS_ERROR, KERNEL_STATUS_NOINTERNET, KERNEL_STATUS_RUNNING

from train_runner import connection

import threading

class Task:
    def __init__(self, task, sleep=None):
        self.task = task
        self.time_to_run = time.time() + sleep

    def run(self):
        self.task()

def kernel_status_request_task(kernel: Kernel, on_complete, wait=300):
    def task():
        while True:
            status = kernel.get_status()

            if status != KERNEL_STATUS_NOINTERNET:
                on_complete(kernel, status)

                break

            else:
                print(status)

    return Task(task, wait)

def kernel_run_request_task(kernel: Kernel, wait=300):
    def task():
        kernel.push()

    return Task(task, wait)

class MainLoop:
    def __init__(self, project: Project):
        self.project = project

        self.queue = []

        self.running = 0

        self.wait = self.project.meta["requests_delay"]

        self.kernels_queue = None

    def add_task(self, task):
        self.queue.insert(0, task)

    def run_server(self):
        def do_run_server():
            connection.run_server(self.project)

        threading.Thread(target=do_run_server).start()

    def shutdown(self):
        self.project.server.shutdown()
        self.project.server.server_close()

    def start(self):
        self.run_server()

        self.kernels_queue = list(self.project.kernels)

        self.add_kernels()

        while True:
            if len(self.queue) > 0:
                task = self.queue.pop()

                if time.time() > task.time_to_run:
                    task.run()
                else:
                    self.add_task(task)

                time.sleep(1)

            else:
                self.shutdown()

                break

    def add_kernels(self):
        while len(self.kernels_queue) and self.running < self.project.meta["kernels"]:
            self.running += 1

            self.add_task(kernel_status_request_task(self.kernels_queue.pop(), self.on_kernel_status, 10));

    def run_kernel(self, kernel, wait_after_run, wait_after_status, is_initial):
        kernel.archive(is_initial)

        self.add_task(kernel_run_request_task(kernel, wait_after_run))

        self.add_task(kernel_status_request_task(kernel, self.on_kernel_status, wait_after_status))

    def on_kernel_status(self, kernel, status):
        print("status: " + status)

        if status == KERNEL_STATUS_UNKNOWN:
            self.run_kernel(kernel, 10, 20, True)

            return

        if status == KERNEL_STATUS_COMPLETE or status == KERNEL_STATUS_ERROR:
            kernel.download()

            if kernel.is_complete():
                self.running -= 1

                self.add_kernels()
            else:
                self.run_kernel(kernel, self.wait, self.wait, False)
            return

        if status == KERNEL_STATUS_RUNNING:
            self.add_task(kernel_status_request_task(kernel, self.on_kernel_status))

            return

pass

MainLoop(Project("/Users/dreamflyer/Desktop/kaggle_project/project")).start()



