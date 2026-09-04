from app.main import main


def test_main_runs_without_error() -> None:
    assert main() is None
