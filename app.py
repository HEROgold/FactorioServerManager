"""The module where the required objects are defined for running a web server."""

from flask import Flask
from flask_login import LoginManager  # type: ignore[no-stub-file]


app = Flask(__name__)
lm = LoginManager(app)


def main() -> None:  # noqa: D103
    app.run()


if __name__ == "__main__":
    main()
