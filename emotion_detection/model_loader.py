# emotion_detection/model_loader.py

from __future__ import annotations

from functools import lru_cache
import importlib.util


def _load_fer_class():
    try:
        from fer.fer import FER as fer_class
        return fer_class
    except ModuleNotFoundError as exc:
        if exc.name == "pkg_resources":
            raise RuntimeError(
                "The installed fer package requires setuptools. "
                "Install setuptools in the active virtual environment."
            ) from exc
        if exc.name not in {"fer", "fer.fer"}:
            raise
    except ImportError:
        pass

    try:
        from fer import FER as fer_class
        return fer_class
    except ModuleNotFoundError as exc:
        if exc.name == "pkg_resources":
            raise RuntimeError(
                "The installed fer package requires setuptools. "
                "Install setuptools in the active virtual environment."
            ) from exc
        raise RuntimeError(
            "Unable to import FER from the installed fer package."
        ) from exc
    except ImportError as exc:
        raise RuntimeError(
            "Unable to import FER from the installed fer package."
        ) from exc


@lru_cache(maxsize=1)
def load_emotion_model():
    fer_class = _load_fer_class()

    # Prefer facenet-pytorch when available, otherwise fall back to Haar cascade.
    use_mtcnn = importlib.util.find_spec("facenet_pytorch") is not None

    return fer_class(mtcnn=use_mtcnn)
