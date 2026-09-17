from bridge.dialogue import bounded_dialogue


def test_relay_preserves_multi_turn_roles_and_one_system_owner():
    dialogue = [
        {"role": "system", "content": "server persona"},
        {"role": "user", "content": "My made-up name is Quill."},
        {"role": "assistant", "content": "Nice to meet you, Quill."},
        {"role": "user", "content": "What name did I give you?"},
    ]
    assert bounded_dialogue(dialogue, max_messages=8) == dialogue


def test_relay_bounds_old_turns_but_keeps_system_and_latest_complete_turns():
    dialogue = [{"role": "system", "content": "persona"}] + [
        {"role": "user" if i % 2 == 0 else "assistant", "content": str(i)}
        for i in range(10)
    ]
    result = bounded_dialogue(dialogue, max_messages=5)
    assert result[0] == {"role": "system", "content": "persona"}
    assert [m["content"] for m in result[1:]] == ["6", "7", "8", "9"]


def test_relay_drops_unknown_roles_and_empty_content():
    assert bounded_dialogue([
        {"role": "tool", "content": "not portable"},
        {"role": "user", "content": ""},
        {"role": "user", "content": "hello"},
    ]) == [{"role": "user", "content": "hello"}]


def test_request_always_contains_current_turn_without_duplicating_it():
    from bridge.dialogue import dialogue_for_turn
    system = {'role': 'system', 'content': 'server persona'}
    current = {'role': 'user', 'content': 'hello'}
    assert dialogue_for_turn([system], 'hello', 'fallback') == [system, current]
    assert dialogue_for_turn([system, current], 'hello', 'fallback') == [system, current]
    assert dialogue_for_turn([], 'hello', 'fallback')[-1] == current
    assert dialogue_for_turn([{'role': 'assistant', 'content': 'previous'}], 'hello', 'fallback')[-1] == current
