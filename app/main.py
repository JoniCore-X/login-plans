from app.bootstrap.application import Application
from app.core.config import get_settings


def main() -> None:
    settings = get_settings()

    application = Application(settings)

    application.start()


if __name__ == "__main__":
    main()
