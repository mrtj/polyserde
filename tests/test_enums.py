"""Tests for enum serialization and deserialization."""

import pytest
from polyserde import PolymorphicSerde
from tests.conftest import Color, Priority


class TestEnumSerialization:
    """Test enum serialization."""

    def test_serialize_string_enum(self):
        result = PolymorphicSerde._to_json(Color.RED)

        assert isinstance(result, dict)
        assert "__enum__" in result
        assert result["__enum__"] == "tests.conftest.Color.RED"

    def test_serialize_int_enum(self):
        result = PolymorphicSerde._to_json(Priority.HIGH)

        assert isinstance(result, dict)
        assert result["__enum__"] == "tests.conftest.Priority.HIGH"

    def test_serialize_all_color_values(self):
        """Test all enum members serialize correctly."""
        colors = [Color.RED, Color.GREEN, Color.BLUE]
        results = [PolymorphicSerde._to_json(c) for c in colors]

        assert results[0]["__enum__"] == "tests.conftest.Color.RED"
        assert results[1]["__enum__"] == "tests.conftest.Color.GREEN"
        assert results[2]["__enum__"] == "tests.conftest.Color.BLUE"


class TestEnumDeserialization:
    """Test enum deserialization."""

    def test_deserialize_string_enum(self):
        data = {"__enum__": "tests.conftest.Color.RED"}
        result = PolymorphicSerde._from_json(data)

        assert result == Color.RED
        assert isinstance(result, Color)

    def test_deserialize_int_enum(self):
        data = {"__enum__": "tests.conftest.Priority.MEDIUM"}
        result = PolymorphicSerde._from_json(data)

        assert result == Priority.MEDIUM
        assert isinstance(result, Priority)
        assert result.value == 2

    def test_deserialize_all_priority_values(self):
        """Test all enum members deserialize correctly."""
        data = [
            {"__enum__": "tests.conftest.Priority.LOW"},
            {"__enum__": "tests.conftest.Priority.MEDIUM"},
            {"__enum__": "tests.conftest.Priority.HIGH"},
        ]
        results = [PolymorphicSerde._from_json(d) for d in data]

        assert results[0] == Priority.LOW
        assert results[1] == Priority.MEDIUM
        assert results[2] == Priority.HIGH


class TestEnumRoundtrip:
    """Test enum roundtrip serialization."""

    def test_roundtrip_color_enum(self):
        original = Color.BLUE
        serialized = PolymorphicSerde._to_json(original)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert deserialized == original
        assert type(deserialized) is Color

    def test_roundtrip_priority_enum(self):
        original = Priority.HIGH
        serialized = PolymorphicSerde._to_json(original)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert deserialized == original
        assert deserialized.value == 3

    def test_roundtrip_enum_list(self):
        """Test list of enums."""
        original = [Color.RED, Color.BLUE, Color.GREEN]
        serialized = PolymorphicSerde._to_json(original)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert len(deserialized) == 3
        assert deserialized[0] == Color.RED
        assert deserialized[1] == Color.BLUE
        assert deserialized[2] == Color.GREEN


class TestEnumsInModels:
    """Test enums as fields in Pydantic models."""

    def test_model_with_enum_field(self, config_with_enums):
        """Test configuration model with enum fields."""
        serialized = PolymorphicSerde._to_json(config_with_enums)

        assert serialized["name"] == "test_config"
        assert serialized["priority"]["__enum__"] == "tests.conftest.Priority.HIGH"
        assert len(serialized["colors"]) == 2
        assert serialized["colors"][0]["__enum__"] == "tests.conftest.Color.RED"

    def test_roundtrip_model_with_enums(self, config_with_enums):
        """Full roundtrip of model containing enums."""
        serialized = PolymorphicSerde._to_json(config_with_enums)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert deserialized.name == "test_config"
        assert deserialized.priority == Priority.HIGH
        assert len(deserialized.colors) == 2
        assert deserialized.colors[0] == Color.RED
        assert deserialized.colors[1] == Color.BLUE

    def test_enum_in_dict_value(self):
        """Test enums as dictionary values."""
        from tests.conftest import Settings

        settings = Settings(theme={"primary": Color.BLUE, "secondary": Color.GREEN})
        serialized = PolymorphicSerde._to_json(settings)
        deserialized = PolymorphicSerde._from_json(serialized)

        # Access the theme dict values
        theme_items = list(deserialized.theme.values())
        assert Color.BLUE in theme_items
        assert Color.GREEN in theme_items


class TestEnumEdgeCases:
    """Edge cases for enum handling."""

    def test_enum_with_duplicate_values(self):
        """Test enums with duplicate values (aliases)."""
        from tests.conftest import Status

        # WAITING is an alias for PENDING
        serialized = PolymorphicSerde._to_json(Status.WAITING)
        deserialized = PolymorphicSerde._from_json(serialized)

        # Should deserialize to the canonical member (PENDING)
        assert deserialized.value == 1
        # Note: aliases resolve to the first member with that value
        assert deserialized.name in ["PENDING", "WAITING"]

    def test_nested_enum_in_list_in_model(self):
        """Test deeply nested enum structures."""
        from tests.conftest import Palette

        palette = Palette(
            color_groups=[
                [Color.RED, Color.GREEN],
                [Color.BLUE],
            ]
        )

        serialized = PolymorphicSerde._to_json(palette)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert len(deserialized.color_groups) == 2
        assert deserialized.color_groups[0][0] == Color.RED
        assert deserialized.color_groups[1][0] == Color.BLUE
