def test_cli_imports():
    from cli.main import app

    assert app is not None
