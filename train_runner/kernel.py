import os

import yaml

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

        self.folds = 0

        self.meta = utils.read_project_meta(self.root)

        self.collect_experiment()

        self.load()

        self.server: socketserver.TCPServer = None

        self.folds = None

    def collect_experiment(self):
        utils.remove(os.path.join(self.root, "kaggle", "project"))

        utils.ensure(os.path.join(self.root, "kaggle"))
        utils.ensure(os.path.join(self.root, "kaggle", "project"))
        utils.ensure(os.path.join(self.root, "kaggle", "project", "experiments"))

        def filter(item):
            if not os.path.isdir(os.path.join(self.root, item)):
                return False

            if item == "experiments":
                return False

            if item == "kaggle":
                return False

            return True

        directories = [item for item in os.listdir(self.root) if filter(item)]

        for item in directories:
            utils.copy(os.path.join(self.root, item), os.path.join(self.root, "kaggle", "project", item))

        utils.copy(os.path.join(self.root, "experiments", self.meta["experiment"]), os.path.join(self.root, "kaggle", "project", "experiments", "experiment"))

        data_name_path = os.path.join(os.path.join(self.root, "kaggle", "project"), "dataset_id.txt")

        if not os.path.exists(data_name_path):
            with open(data_name_path, "w+") as f:
                dataset_id = self.meta["dataset_sources"][0] if len(self.meta["dataset_sources"]) > 0 else self.meta["competition_sources"][0]

                f.write(dataset_id)

    def load(self):
        utils.ensure(os.path.join(self.root, "kaggle"))

        with open(os.path.join(self.root, "experiments", self.meta["experiment"], "config.yaml")) as cfg:
            self.folds = yaml.load(cfg).pop("folds_count", None)

        if self.meta["split_by_folds"]:
            for item in range(self.folds):
                self.kernels.append(Kernel(item, self, item))

            return

        for item in range(self.meta["kernels"]):
            self.kernels.append(Kernel(item, self))

    def kernel(self, id):
        for item in self.kernels:
            if item.id == id:
                return item

class Kernel:
    def __init__(self, id, project, fold=-1):
        self.id = id

        self.project = project

        self.meta = None

        self.fold=fold

        self.load()

    def load(self):
        self.meta = utils.kernel_meta(self.get_path(), self.id, self.project.meta["username"], self.project.meta["server"], self.get_title(), self.project.meta["dataset_sources"], self.project.meta["competition_sources"], self.project.meta["kernel_sources"], self.fold, self.project.meta["time"])

    def get_path(self):
        return os.path.join(self.project.root, "kaggle", "kernels", "kernel_" + str(self.id))

    def get_title(self):
        return self.project.meta["project_id"] + "-" + str(self.id)

    def get_status(self, after_run=False):
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
        generated_project_path = os.path.join(self.get_path(), "project")

        if initial:
            utils.archive(os.path.join(self.project.root, "kaggle", "project"), generated_project_path)

        #utils.write_dataset_meta(self.project.meta["username"], self.get_title(), generated_project_path)

    def log(self, bytes):
        utils.log(os.path.join(self.get_path(), "kernel.log"), bytes)

    def is_complete(self):
        return utils.is_complete(self.get_path())

    def push(self):
        response = utils.run_kernel(self.get_path())

        if len(response) > 0:
            print(response)

    def download(self):
        project_path = os.path.join(self.get_path(), "project")

        utils.remove(project_path)

        utils.download(self.meta["id"], self.get_path())
#
# p = Project("/Users/dreamflyer/Desktop/kaggle_project/project")
#
# for item in p.kernels:
#     item.archive(True)









