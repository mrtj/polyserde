"""Tests for basic serialization of primitives, lists, and dictionaries."""

import pytest
from polyserde import PolymorphicSerde


class TestPrimitives:
    """Test serialization of primitive types."""

    def test_serialize_string(self):
        result = PolymorphicSerde._to_json("hello")
        assert result == "hello"

    def test_serialize_int(self):
        result = PolymorphicSerde._to_json(42)
        assert result == 42

    def test_serialize_float(self):
        result = PolymorphicSerde._to_json(3.14)
        assert result == 3.14

    def test_serialize_bool_true(self):
        result = PolymorphicSerde._to_json(True)
        assert result is True

    def test_serialize_bool_false(self):
        result = PolymorphicSerde._to_json(False)
        assert result is False

    def test_serialize_none(self):
        result = PolymorphicSerde._to_json(None)
        assert result is None

    def test_deserialize_string(self):
        result = PolymorphicSerde._from_json("hello")
        assert result == "hello"

    def test_deserialize_int(self):
        result = PolymorphicSerde._from_json(42)
        assert result == 42

    def test_deserialize_float(self):
        result = PolymorphicSerde._from_json(3.14)
        assert result == 3.14

    def test_deserialize_bool(self):
        result = PolymorphicSerde._from_json(True)
        assert result is True

    def test_deserialize_none(self):
        result = PolymorphicSerde._from_json(None)
        assert result is None


class TestLists:
    """Test serialization of lists."""

    def test_serialize_empty_list(self):
        result = PolymorphicSerde._to_json([])
        assert result == []

    def test_serialize_list_of_ints(self):
        result = PolymorphicSerde._to_json([1, 2, 3, 4, 5])
        assert result == [1, 2, 3, 4, 5]

    def test_serialize_list_of_strings(self):
        result = PolymorphicSerde._to_json(["a", "b", "c"])
        assert result == ["a", "b", "c"]

    def test_serialize_mixed_list(self):
        result = PolymorphicSerde._to_json([1, "hello", 3.14, True, None])
        assert result == [1, "hello", 3.14, True, None]

    def test_serialize_nested_list(self):
        result = PolymorphicSerde._to_json([[1, 2], [3, 4], [5]])
        assert result == [[1, 2], [3, 4], [5]]

    def test_deserialize_empty_list(self):
        result = PolymorphicSerde._from_json([])
        assert result == []

    def test_deserialize_list_of_ints(self):
        result = PolymorphicSerde._from_json([1, 2, 3])
        assert result == [1, 2, 3]

    def test_deserialize_nested_list(self):
        result = PolymorphicSerde._from_json([[1, 2], [3, 4]])
        assert result == [[1, 2], [3, 4]]


class TestTuples:
    """Test serialization of tuples (preserved with __tuple__ marker)."""

    def test_serialize_empty_tuple(self):
        result = PolymorphicSerde._to_json(())
        assert result == {"__tuple__": []}

    def test_serialize_tuple(self):
        result = PolymorphicSerde._to_json((1, 2, 3))
        assert result == {"__tuple__": [1, 2, 3]}

    def test_serialize_nested_tuple(self):
        result = PolymorphicSerde._to_json(((1, 2), (3, 4)))
        assert result == {"__tuple__": [{"__tuple__": [1, 2]}, {"__tuple__": [3, 4]}]}

    def test_roundtrip_tuple_preserved(self):
        """Tuples are now preserved through serialization."""
        original = (1, 2, 3)
        serialized = PolymorphicSerde._to_json(original)
        deserialized = PolymorphicSerde._from_json(serialized)
        assert deserialized == (1, 2, 3)  # Stays as tuple
        assert type(deserialized) is tuple


class TestSimpleDictionaries:
    """Test serialization of dictionaries with string keys."""

    def test_serialize_empty_dict(self):
        result = PolymorphicSerde._to_json({})
        # Empty dict with string keys
        expected = {"__dict__": []}
        assert result == expected

    def test_serialize_string_key_dict(self):
        result = PolymorphicSerde._to_json({"a": 1, "b": 2})
        # Dict with simple keys gets the __dict__ wrapper
        assert "__dict__" in result
        items = result["__dict__"]
        assert len(items) == 2

    def test_serialize_nested_dict(self):
        data = {"outer": {"inner": 42}}
        result = PolymorphicSerde._to_json(data)
        assert "__dict__" in result

    def test_deserialize_empty_dict(self):
        serialized = {"__dict__": []}
        result = PolymorphicSerde._from_json(serialized)
        assert result == {}

    def test_roundtrip_string_key_dict(self):
        original = {"name": "Alice", "age": 30}
        serialized = PolymorphicSerde._to_json(original)
        deserialized = PolymorphicSerde._from_json(serialized)
        assert deserialized == original
