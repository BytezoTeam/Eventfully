from typing import Callable

from result import Result

from eventfully.data.emails import main as get_emails
from eventfully.data.zuerichunbezahlbar_ch import main as get_zuerichunbezahlbar_ch

# Add new sources here
sources: list[Callable[[], Result[None, Exception]]] = [
    get_emails,
    get_zuerichunbezahlbar_ch
]


def main():
    for source in sources:
        result = source()
        if result.is_err():
            print(str(result.err()))


if __name__ == "__main__":
    main()
