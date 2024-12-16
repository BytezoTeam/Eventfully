import pytest

from eventfully.utils import extract_language_from_language_header


@pytest.mark.parametrize(
    "language_header,accepted_languages,expected_result",
    [
        ("en", ("en",), "en"),
        ("de-DE,de;q=0.9", ("en", "de"), "de"),
        ("de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7", ("en", "de"), "de"),
    ],
)
def test_extract_language_from_language_header(language_header: str, accepted_languages: tuple, expected_result: str):
    assert extract_language_from_language_header(language_header, accepted_languages) == expected_result
