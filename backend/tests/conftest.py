import os
import sys

import pytest

# Permite importar app.py e validacao.py a partir da pasta backend/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app  # noqa: E402


@pytest.fixture
def client():
    flask_app.config.update(TESTING=False, PROPAGATE_EXCEPTIONS=False)
    return flask_app.test_client()
