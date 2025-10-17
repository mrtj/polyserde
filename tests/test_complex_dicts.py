"""Tests for dictionaries with complex (non-string) keys."""

import pytest
from polyserde import PolymorphicSerde
from tests.conftest import Color, Priority


class TestComplexDictKeys:
    """Test dictionaries with non-string keys."""

    def test_dict_with_int_keys(self):
        data = {1: "one", 2: "two", 3: "three"}
        serialized = PolymorphicSerde._to_json(data)

        assert "__dict__" in serialized
        assert len(serialized["__dict__"]) == 3

        # Verify structure
        for item in serialized["__dict__"]:
            assert "__key__" in item
            assert "value" in item

    def test_dict_with_tuple_keys(self):
        data = {(1, 2): "pair1", (3, 4): "pair2"}
        serialized = PolymorphicSerde._to_json(data)

        assert "__dict__" in serialized
        assert len(serialized["__dict__"]) == 2

    def test_dict_with_enum_keys(self):
        data = {Color.RED: "stop", Color.GREEN: "go", Color.BLUE: "caution"}
        serialized = PolymorphicSerde._to_json(data)

        assert "__dict__" in serialized
        items = serialized["__dict__"]

        # Check that enum keys are serialized with __enum__
        for item in items:
            assert "__enum__" in item["__key__"]

    def test_dict_with_mixed_key_types(self):
        """Test dict with multiple different key types."""
        data = {
            1: "int key",
            "string": "string key",
            (1, 2): "tuple key",
            Color.RED: "enum key"
        }
        serialized = PolymorphicSerde._to_json(data)

        assert "__dict__" in serialized
        assert len(serialized["__dict__"]) == 4


class TestComplexDictDeserialization:
    """Test deserialization of dicts with complex keys."""

    def test_deserialize_int_keys(self):
        serialized = {
            "__dict__": [
                {"__key__": 1, "value": "one"},
                {"__key__": 2, "value": "two"}
            ]
        }
        result = PolymorphicSerde._from_json(serialized)

        assert result == {1: "one", 2: "two"}
        assert isinstance(result, dict)

    def test_deserialize_tuple_keys(self):
        serialized = {
            "__dict__": [
                {"__key__": [1, 2], "value": "pair1"},
                {"__key__": [3, 4], "value": "pair2"}
            ]
        }
        result = PolymorphicSerde._from_json(serialized)

        # Lists as keys are automatically converted to tuples
        assert result == {(1, 2): "pair1", (3, 4): "pair2"}

    def test_deserialize_enum_keys(self):
        serialized = {
            "__dict__": [
                {"__key__": {"__enum__": "tests.conftest.Color.RED"}, "value": "stop"},
                {"__key__": {"__enum__": "tests.conftest.Color.GREEN"}, "value": "go"}
            ]
        }
        result = PolymorphicSerde._from_json(serialized)

        assert result[Color.RED] == "stop"
        assert result[Color.GREEN] == "go"


class TestComplexDictRoundtrip:
    """Test roundtrip serialization of complex dicts."""

    def test_roundtrip_int_keys(self):
        original = {1: "one", 2: "two", 3: "three"}
        serialized = PolymorphicSerde._to_json(original)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert deserialized == original

    def test_roundtrip_enum_keys(self):
        original = {Color.RED: "stop", Color.GREEN: "go", Color.BLUE: "caution"}
        serialized = PolymorphicSerde._to_json(original)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert len(deserialized) == 3
        assert deserialized[Color.RED] == "stop"
        assert deserialized[Color.GREEN] == "go"
        assert deserialized[Color.BLUE] == "caution"

    def test_roundtrip_tuple_keys(self):
        original = {(1, 2): "a", (3, 4): "b"}
        serialized = PolymorphicSerde._to_json(original)
        deserialized = PolymorphicSerde._from_json(serialized)

        # Tuples are now preserved as dict keys
        assert deserialized == original
        assert (1, 2) in deserialized
        assert (3, 4) in deserialized

    def test_roundtrip_mixed_keys(self):
        """Roundtrip with various key types."""
        original = {
            1: "int",
            "str": "string",
            Color.RED: "enum",
        }
        serialized = PolymorphicSerde._to_json(original)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert deserialized[1] == "int"
        assert deserialized["str"] == "string"
        assert deserialized[Color.RED] == "enum"


class TestComplexDictValues:
    """Test dicts with complex values (models, enums, etc)."""

    def test_dict_with_model_values(self):
        from tests.conftest import Person

        data = {
            "alice": Person(name="Alice", age=30),
            "bob": Person(name="Bob", age=25)
        }

        serialized = PolymorphicSerde._to_json(data)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert isinstance(deserialized["alice"], Person)
        assert deserialized["alice"].name == "Alice"
        assert deserialized["bob"].age == 25

    def test_dict_with_enum_values(self):
        data = {"primary": Color.BLUE, "secondary": Color.GREEN}

        serialized = PolymorphicSerde._to_json(data)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert deserialized["primary"] == Color.BLUE
        assert deserialized["secondary"] == Color.GREEN

    def test_dict_with_nested_dict_values(self):
        data = {
            "outer1": {"inner": 42},
            "outer2": {"nested": {"deep": "value"}}
        }

        serialized = PolymorphicSerde._to_json(data)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert deserialized["outer1"]["inner"] == 42
        assert deserialized["outer2"]["nested"]["deep"] == "value"


class TestDictInModels:
    """Test dicts with complex keys inside Pydantic models."""

    def test_model_with_complex_dict_field(self):
        from tests.conftest import Mapping

        mapping = Mapping(
            color_codes={
                Color.RED: "#FF0000",
                Color.GREEN: "#00FF00",
                Color.BLUE: "#0000FF"
            }
        )

        serialized = PolymorphicSerde._to_json(mapping)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert deserialized.color_codes[Color.RED] == "#FF0000"
        assert deserialized.color_codes[Color.GREEN] == "#00FF00"

    def test_model_with_int_key_dict(self):
        from tests.conftest import IndexedData

        data = IndexedData(items={0: "first", 1: "second", 2: "third"})

        serialized = PolymorphicSerde._to_json(data)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert deserialized.items[0] == "first"
        assert deserialized.items[1] == "second"
        assert deserialized.items[2] == "third"


class TestEdgeCasesComplexDicts:
    """Edge cases for complex dictionary handling."""

    def test_empty_dict_with_dict_wrapper(self):
        data = {}
        serialized = PolymorphicSerde._to_json(data)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert deserialized == {}

    def test_deeply_nested_dicts_with_complex_keys(self):
        """Test nested structure with multiple levels of complex keys."""
        data = {
            Color.RED: {
                Priority.HIGH: "urgent",
                Priority.LOW: "not urgent"
            },
            Color.BLUE: {
                Priority.MEDIUM: "moderate"
            }
        }

        serialized = PolymorphicSerde._to_json(data)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert deserialized[Color.RED][Priority.HIGH] == "urgent"
        assert deserialized[Color.RED][Priority.LOW] == "not urgent"
        assert deserialized[Color.BLUE][Priority.MEDIUM] == "moderate"

    def test_dict_keys_and_values_both_complex(self):
        """Test dict where both keys and values are complex types."""
        from tests.conftest import Person

        data = {
            Color.RED: Person(name="Red Person", age=25),
            Color.BLUE: Person(name="Blue Person", age=30)
        }

        serialized = PolymorphicSerde._to_json(data)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert isinstance(deserialized[Color.RED], Person)
        assert deserialized[Color.RED].name == "Red Person"
        assert deserialized[Color.BLUE].age == 30
