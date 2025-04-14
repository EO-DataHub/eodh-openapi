from eodh_openapi import utils


def test_get_nested_key__key_exists__dict_not_modified():
    d = {"a": {"b": {"c": "value"}}}
    key = "a.b.c"
    result = utils.get_nested_key(d, key)
    assert result == "value"
    assert d == {"a": {"b": {"c": "value"}}}


def test_get_nested_key__key_does_not_exist__dict_modified():
    d = {"a": {"b": {"c": "value"}}}
    key = "a.d.e"
    result = utils.get_nested_key(d, key, default="test")
    assert result == "test"
    assert d == {"a": {"b": {"c": "value"}, "d": {"e": "test"}}}


def test_get_nested_key__key_does_not_exist__dict_modified_empty():
    d = {}
    key = "a.d.e"
    result = utils.get_nested_key(d, key, default="test")
    assert result == "test"
    assert d == {"a": {"d": {"e": "test"}}}


def test_recursive_merge__no_conflicts__success():
    d1 = {
        "a": {"b": {"c": "value"}},
        "x": {"y": {"z": "other_value"}},
    }
    d2 = {
        "a": {"b": {"d": "new_value"}},
        "x": {"y": {"w": "another_value"}},
    }
    result = utils.recursive_merge(d1, d2)
    assert result == {
        "a": {"b": {"c": "value", "d": "new_value"}},
        "x": {"y": {"z": "other_value", "w": "another_value"}},
    }


def test_recursive_merge__conflict__overwrite():
    d1 = {
        "a": {"b": {"c": "value"}},
        "x": {"y": {"z": "other_value"}},
    }
    d2 = {
        "a": {"b": {"d": "new_value"}},
        "x": {"y": {"z": "another_value"}},
    }
    result = utils.recursive_merge(d1, d2)
    assert result == {
        "a": {"b": {"c": "value", "d": "new_value"}},
        "x": {"y": {"z": "another_value"}},
    }
