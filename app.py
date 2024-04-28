"""The module where the required objects are defined for running a web server."""


from routes import app


def main() -> None:  # noqa: D103
    app.run()


if __name__ == "__main__":
    main()
