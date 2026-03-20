import importlib


def test_sitecustomize_applies_safe_patch():
    mod = importlib.import_module("ia_leg.rag.answer_engine")
    assert getattr(mod, "_IA_LEG_SAFE_PATCHED", False) is True
