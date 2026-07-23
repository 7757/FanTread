import random
import string

from fantread.cleaner import normalize_text, remove_noise, split_text
from fantread.extractor import ArticleExtractor, ExtractionError


def test_randomized_text_operations_preserve_invariants() -> None:
    randomizer = random.Random(20260723)
    atoms = (
        "中文",
        "alpha",
        "42",
        "。",
        ".",
        "！",
        "?",
        "\n",
        "\n\n",
        "  ",
        "\t",
        "🙂",
        "`cmd`",
    )

    for _ in range(300):
        source = "".join(
            randomizer.choice(atoms) for _ in range(randomizer.randint(0, 400))
        )
        target = randomizer.randint(1, 160)
        normalized = normalize_text(source)
        chunks = split_text(source, target_chars=target)

        assert "".join(chunks) == normalized
        assert all(0 < len(chunk) <= target for chunk in chunks)
        cleaned = remove_noise(source)
        assert remove_noise(cleaned) == cleaned


def test_randomized_url_inputs_never_leak_parser_exceptions() -> None:
    randomizer = random.Random(8675309)

    for _ in range(500):
        source = "".join(
            randomizer.choice(string.printable)
            for _ in range(randomizer.randint(0, 80))
        )
        try:
            normalized = ArticleExtractor.normalize_url(source)
        except ExtractionError:
            continue
        assert normalized.startswith(("http://", "https://"))
