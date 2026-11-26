import pytest

from library_app.library import Library
from library_app.models import Book


@pytest.fixture
def data_dir(tmp_path):
    return tmp_path / "data"


@pytest.fixture
def empty_library(data_dir):
    return Library(data_dir)


@pytest.fixture
def sample_book():
    return Book("Война и мир", "Толстой", 1869, "роман", 1225, "прочитана", 5)


@pytest.fixture
def library_with_books(empty_library, sample_book):
    empty_library.add_book(sample_book)
    empty_library.add_book(Book("Мастер и Маргарита", "Булгаков", 1967, "роман", 480))
    return empty_library

def pytest_report_teststatus(report, config):
    if report.when == "call":
        node = config.pluginmanager.getplugin("terminalreporter")
        for key, value in report.user_properties:
            if key == "doc" and value:
                return report.outcome, report.outcome[0].upper(), f"{report.outcome.upper()} ({value})"


def pytest_runtest_makereport(item, call):
    if call.when == "call" and item.obj.__doc__:
        item.user_properties.append(("doc", item.obj.__doc__.strip()))

_last_module = None


def pytest_runtest_logstart(nodeid, location):
    global _last_module
    module_name = nodeid.split("::")[0]
    if module_name != _last_module:
        _last_module = module_name
        print(f"\n\n{'=' * 70}\n  Файл: {module_name}\n{'=' * 70}")

