def test_safe_dashboard_entrypoint_imports():
    import dashboard.app_safe  # noqa: F401


def test_safe_pipeline_has_processar_tudo():
    from etl.versionamento_pipeline_safe import processar_tudo

    assert callable(processar_tudo)
