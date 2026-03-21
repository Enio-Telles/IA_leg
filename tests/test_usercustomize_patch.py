import importlib


def test_usercustomize_applies_audited_patch():
    importlib.import_module("usercustomize")
    mod = importlib.import_module("ia_leg.rag.answer_engine")
    assert getattr(mod, "_IA_LEG_SAFE_AUDITED_PATCHED", False) is True
