from typing import Callable

from result import Result

from eventfully.data.emails import get_emails
from eventfully.data.zuerichunbezahlbar_ch import get_zuerichunbezahlbar

# Add new sources here
sources: list[Callable[[], Result[None, Exception]]] = [
    get_emails,
    get_zuerichunbezahlbar
]


def main():
    for source in sources:
        source_name = source.__name__

        print(f"Running {source_name} ...")
        result = source()
        if result.is_err():
            print(f"[ERROR] {source_name} {str(result.err())}")


if __name__ == "__main__":
    main()
