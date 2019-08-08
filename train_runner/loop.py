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

        for item in self.project.kernels:
            self.add_task(kernel_status_request_task(item, self.on_kernel_status, 10));

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

    def on_kernel_status(self, kernel, status):
        print("status: " + status)

        if status == KERNEL_STATUS_UNKNOWN:
            kernel.archive(True)

            self.add_task(kernel_run_request_task(kernel, 10))

            self.add_task(kernel_status_request_task(kernel, self.on_kernel_status, 20))

            return

        if status == KERNEL_STATUS_COMPLETE:
            kernel.download()

            if not kernel.is_complete():
                kernel.archive()

                self.add_task(kernel_run_request_task(kernel))

                self.add_task(kernel_status_request_task(kernel, self.on_kernel_status))

            return

        if status == KERNEL_STATUS_ERROR:
            kernel.download()

            if not kernel.is_complete():
                kernel.archive()

                self.add_task(kernel_run_request_task(kernel))

                self.add_task(kernel_status_request_task(kernel, self.on_kernel_status))

            return

        if status == KERNEL_STATUS_RUNNING:
            self.add_task(kernel_status_request_task(kernel, self.on_kernel_status))

            return

MainLoop(Project("/Users/dreamflyer/Desktop/kaggle_project")).start()



