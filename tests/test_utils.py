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


def test_update_tags__no_conflicts():
    tags = [{"name": "tag1", "description": "description1"}]
    new_tags = [{"name": "tag2", "description": "description2"}]
    result = utils.update_tags(tags, new_tags)
    assert result == [
        {"name": "tag1", "description": "description1"},
        {"name": "tag2", "description": "description2"},
    ]


def test_update_tags__conflict():
    tags = [{"name": "tag1", "description": "description1"}]
    new_tags = [
        {"name": "tag1", "description": "new_description"},
        {"name": "tag2", "description": "description2"},
    ]
    result = utils.update_tags(tags, new_tags)
    assert result == [
        {"name": "tag1", "description": "new_description"},
        {"name": "tag2", "description": "description2"},
    ]


def test_operations_filter__filter_methods_only():
    path_definition = {
        "summary": "Summary",
        "get": {"summary": "Get"},
        "post": {"summary": "Post"},
        "delete": {"summary": "Delete"},
    }
    filter = utils.Config.APISource.OperationsFilter(methods={"get", "post"})
    result = dict(filter(path_definition))
    assert result == {"get": {"summary": "Get"}, "post": {"summary": "Post"}}


def test_operations_filter__filter_tags_only():
    path_definition = {
        "summary": "Summary",
        "get": {"summary": "Get", "tags": ["tag1"]},
        "post": {"summary": "Post", "tags": ["tag2"]},
        "delete": {"summary": "Delete", "tags": ["tag1"]},
    }
    filter = utils.Config.APISource.OperationsFilter(tags={"tag1"})
    result = dict(filter(path_definition))
    assert result == {
        "get": {"summary": "Get", "tags": ["tag1"]},
        "delete": {"summary": "Delete", "tags": ["tag1"]},
    }
