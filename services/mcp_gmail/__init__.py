from . import schemas, gmail_api
__all__ = ["schemas", "gmail_api"]

if __name__ == "__main__":
    from .server import main
    main()
