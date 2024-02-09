from typing import Callable

from result import Result

from .emails import main as get_emails

# Add new sources here
sources: list[Callable[[], Result]] = [
    get_emails
]


def main():
    for source in sources:
        result = source()
        if result.is_err():
            print(result.err())


if __name__ == "__main__":
    main()
