import os

from train_runner import utils

import socketserver

KERNEL_STATUS_RUNNING = "running"
KERNEL_STATUS_ERROR = "error"
KERNEL_STATUS_CANCELED = "cancel"
KERNEL_STATUS_COMPLETE = "complete"
KERNEL_STATUS_UNKNOWN = "404"
KERNEL_STATUS_NOINTERNET = "nointernet"

class Project:
    def __init__(self, root):
        self.root = root

        self.meta = None

        self.kernels = []

        self.load()

        self.server: socketserver.TCPServer = None

    def load(self):
        self.meta = utils.read_project_meta(self.root)

        for item in range(self.meta["kernels"]):
            self.kernels.append(Kernel(item, self))

    def kernel(self, id):
        for item in self.kernels:
            if item.id == id:
                return item

class Kernel:
    def __init__(self, id, project):
        self.id = id

        self.project = project

        self.meta = None

        self.load()

    def load(self):
        self.meta = utils.kernel_meta(self.get_path(), self.id, self.project.meta["username"], self.project.meta["server"], self.get_title())

    def get_path(self):
        return os.path.join(self.project.root, "kernel_" + str(self.id))

    def get_title(self):
        return self.project.meta["project_id"] + "-" + str(self.id)

    def get_status(self):
        return self.parse_status(utils.get_status(self.meta["id"]))

    def parse_status(self, status_text):
        if "404 - Not Found" in status_text:
            return KERNEL_STATUS_UNKNOWN

        if "Failed to establish a new connection" in status_text:
            return KERNEL_STATUS_NOINTERNET

        if 'has status "error"' in status_text:
            return KERNEL_STATUS_ERROR

        if 'has status "running"' in status_text:
            return KERNEL_STATUS_RUNNING

        if 'has status "complete"' in status_text:
            return KERNEL_STATUS_COMPLETE

        if 'has status "cancelAcknowledged"' in status_text:
            return KERNEL_STATUS_CANCELED

        return status_text

    def archive(self, initial=False):
        if initial:
            return utils.archive(os.path.join(self.project.root, "project"), os.path.join(self.get_path(), "project"))

        return utils.archive(os.path.join(self.get_path(), "project"), os.path.join(self.get_path(), "project"))

    def is_complete(self):
        pass

    def push(self):
        utils.run_kernel(self.get_path())

    def download(self):
        utils.download(self.meta["id"], self.get_path())









