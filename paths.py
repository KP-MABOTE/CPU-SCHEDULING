"""Single place that decides where every generated output is saved."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")


def _path(subfolder, filename):
    folder = os.path.join(RESULTS_DIR, subfolder)
    os.makedirs(folder, exist_ok=True)          # create the folder if it doesn't exist yet
    return os.path.join(folder, filename)


def csv_path(filename):
    return _path("csv", filename)


def chart_path(filename):
    return _path("charts", filename)


def gantt_path(filename):
    return _path("gantt", filename)