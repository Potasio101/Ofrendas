from offering_app.strategies.fuzzy_correction import FuzzyCorrection


def test_amount_field_is_normalized_to_numeric_text():
    strategy = FuzzyCorrection()

    value, confidence = strategy.correct("$1,234.50", "diezmo", [])

    assert value == "1234.50"
    assert confidence >= 0.8


def test_member_name_is_matched_to_closest_known_member():
    strategy = FuzzyCorrection()
    members = ["Juan Perez", "Maria Lopez", "Ana Gomez"]

    value, confidence = strategy.correct("Mria Lopez", "member_name", members)

    assert value == "Maria Lopez"
    assert confidence > 0.6


def test_amount_field_handles_spaced_decimal_digits():
    strategy = FuzzyCorrection()

    value, confidence = strategy.correct("55 6e", "ofrenda", [])

    assert value == "55.6"
    assert confidence >= 0.8
