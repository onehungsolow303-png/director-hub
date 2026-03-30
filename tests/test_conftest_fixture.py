"""Verify conftest has auto-start fixture."""

def test_conftest_has_ensure_services_fixture():
    """conftest should define an ensure_services session fixture."""
    import conftest
    # The fixture function exists
    assert hasattr(conftest, "ensure_services_ready")
