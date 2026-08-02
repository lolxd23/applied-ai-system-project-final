from ai_coach import expected_direction, hint_is_consistent


def test_expected_direction_low_guess():
    assert expected_direction(guess=10, secret=50) == "higher"


def test_expected_direction_high_guess():
    assert expected_direction(guess=90, secret=50) == "lower"


def test_consistent_hint_accepted():
    assert hint_is_consistent("higher", guess=10, secret=50)
    assert hint_is_consistent("Lower", guess=90, secret=50)


def test_inconsistent_hint_rejected():
    assert not hint_is_consistent("lower", guess=10, secret=50)
    assert not hint_is_consistent("higher", guess=90, secret=50)