from bridge.idle_policy import idle_enabled, watchdog_seconds


def test_none_means_never_for_both_idle_guards():
    assert idle_enabled(None) is False
    assert watchdog_seconds(None) is None


def test_zero_is_also_never_instead_of_immediate_close():
    assert idle_enabled(0) is False
    assert watchdog_seconds(0) is None


def test_finite_idle_keeps_sixty_second_watchdog_margin():
    assert idle_enabled(300) is True
    assert watchdog_seconds(300) == 360
