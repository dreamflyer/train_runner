import os, subprocess, json, shutil

def run_cmd(cmd):
    result_string = os.popen(cmd).read()

    return result_string

def get_status(kernel_id):
    cmd = "kaggle kernels status " + kernel_id

    print("status_request: " + cmd)

    return run_cmd(cmd)

def run_kernel(kernel_path):
    cmd = "kaggle kernels push -p " + kernel_path

    return run_cmd(cmd)

def get_template():
    with open("data/kernel-metadata-template.json") as template:
        result = json.load(template)

    return result

def get_notebook_template(server, kernel_id, fold=-1, time=-1):
    with open("data/notebook.ipynb") as template:
        result = template.read().replace("server", server).replace("kernel_id", str(kernel_id))

        if fold >= 0:
            result = result.replace("folds_argument", str(fold))

        if time >= 0:
            result = result.replace("timer_argument", str(time))

        return result

def read_project_meta(project_path):
    with open(os.path.join(project_path, "project-metadata.json")) as meta:
        result = json.load(meta)

    return result

def is_complete(path):
    project_path = os.path.join(path, "project")

    experiment_path = os.path.join(project_path, "experiments")
    experiment_path = os.path.join(experiment_path, "experiment")

    in_progress_path = os.path.join(experiment_path, "inProgress.yaml")

    if os.path.exists(in_progress_path):
        return False

    return True

def download(id, dest):
    run_cmd("kaggle kernels output " + id + " -p " + dest)

def kernel_meta(kernel_path, kernel_id, username, server, title, dataset_sources, competition_sources, kernel_sources, fold, time):
    result = get_template()

    result["id"] = username + "/" + title
    result["title"] = title
    result["code_file"] = os.path.join(kernel_path, "notebook.ipynb")

    result["dataset_sources"] = dataset_sources
    result["competition_sources"] = competition_sources
    result["kernel_sources"] = kernel_sources

    ensure(kernel_path)

    with open(os.path.join(kernel_path, "kernel-metadata.json"), "w") as f:
        json.dump(result, f)

    with open(os.path.join(kernel_path, "notebook.ipynb"), "w") as f:
        f.write(get_notebook_template(server, kernel_id, fold, time))

    return result

def ensure(path):
    if os.path.exists(path):
        return

    os.mkdir(path)

def archive(src, dst):
    shutil.make_archive(dst, 'zip', os.path.dirname(src), "project")

def log(path, bytes):
    with open(path, "a") as f:
        f.buffer.write(bytes)

