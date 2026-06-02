def test_cli_imports():
    from cli.main import main
    assert main is not None
