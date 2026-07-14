from __future__ import annotations

import pytest


@pytest.fixture(scope="session", autouse=True)
def qt_application():
    """Provide a single QApplication instance for the whole test session.

    QApplication (not just QCoreApplication) is required by any test that constructs
    a QWidget or drives it via QTest.
    """
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
