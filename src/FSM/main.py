from app import app


def main() -> None:
    app.run(threaded=True)


if __name__ == "__main__":
    main()
