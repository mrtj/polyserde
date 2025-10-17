"""Tests for class reference serialization and deserialization."""

import pytest
from polyserde import PolymorphicSerde


class TestClassReferenceSerialization:
    """Test serialization of class references (type objects)."""

    def test_serialize_builtin_class(self):
        result = PolymorphicSerde._to_json(dict)

        assert isinstance(result, dict)
        assert "__class_ref__" in result
        assert result["__class_ref__"] == "builtins.dict"

    def test_serialize_list_class(self):
        result = PolymorphicSerde._to_json(list)

        assert result["__class_ref__"] == "builtins.list"

    def test_serialize_str_class(self):
        result = PolymorphicSerde._to_json(str)

        assert result["__class_ref__"] == "builtins.str"

    def test_serialize_custom_class(self):
        from tests.conftest import Person

        result = PolymorphicSerde._to_json(Person)

        assert result["__class_ref__"] == "tests.conftest.Person"

    def test_serialize_int_class(self):
        result = PolymorphicSerde._to_json(int)

        assert result["__class_ref__"] == "builtins.int"


class TestClassReferenceDeserialization:
    """Test deserialization of class references."""

    def test_deserialize_dict_class(self):
        data = {"__class_ref__": "builtins.dict"}
        result = PolymorphicSerde._from_json(data)

        assert result is dict
        assert result == dict

    def test_deserialize_list_class(self):
        data = {"__class_ref__": "builtins.list"}
        result = PolymorphicSerde._from_json(data)

        assert result is list

    def test_deserialize_custom_class(self):
        data = {"__class_ref__": "tests.conftest.Person"}
        result = PolymorphicSerde._from_json(data)

        from tests.conftest import Person
        assert result is Person

    def test_deserialize_enum_class(self):
        data = {"__class_ref__": "tests.conftest.Color"}
        result = PolymorphicSerde._from_json(data)

        from tests.conftest import Color
        assert result is Color


class TestClassReferenceRoundtrip:
    """Test roundtrip serialization of class references."""

    def test_roundtrip_builtin_classes(self):
        classes = [dict, list, str, int, float, bool]

        for cls in classes:
            serialized = PolymorphicSerde._to_json(cls)
            deserialized = PolymorphicSerde._from_json(serialized)
            assert deserialized is cls, f"Failed for {cls}"

    def test_roundtrip_custom_class(self):
        from tests.conftest import Person

        serialized = PolymorphicSerde._to_json(Person)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert deserialized is Person

    def test_roundtrip_list_of_classes(self):
        classes = [dict, list, str]
        serialized = PolymorphicSerde._to_json(classes)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert len(deserialized) == 3
        assert deserialized[0] is dict
        assert deserialized[1] is list
        assert deserialized[2] is str


class TestClassReferencesInModels:
    """Test class references as fields in Pydantic models."""

    def test_model_with_class_reference(self, config_with_enums):
        """Test model with class reference field."""
        serialized = PolymorphicSerde._to_json(config_with_enums)

        assert "handler_class" in serialized
        assert serialized["handler_class"]["__class_ref__"] == "builtins.list"

    def test_roundtrip_model_with_class_reference(self, config_with_enums):
        serialized = PolymorphicSerde._to_json(config_with_enums)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert deserialized.handler_class is list

    def test_model_with_multiple_class_refs(self):
        from tests.conftest import Registry

        registry = Registry(
            string_handler=str,
            number_handler=int,
            collection_handler=list
        )

        serialized = PolymorphicSerde._to_json(registry)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert deserialized.string_handler is str
        assert deserialized.number_handler is int
        assert deserialized.collection_handler is list


class TestClassReferenceEdgeCases:
    """Edge cases for class reference handling."""

    def test_class_ref_in_dict_value(self):
        data = {"handlers": {"default": dict, "backup": list}}

        serialized = PolymorphicSerde._to_json(data)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert deserialized["handlers"]["default"] is dict
        assert deserialized["handlers"]["backup"] is list

    def test_class_ref_in_nested_list(self):
        data = [[dict, list], [str, int]]

        serialized = PolymorphicSerde._to_json(data)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert deserialized[0][0] is dict
        assert deserialized[0][1] is list
        assert deserialized[1][0] is str
        assert deserialized[1][1] is int

    def test_mixed_class_refs_and_instances(self):
        """Test list containing both class references and instances."""
        from tests.conftest import Container

        container = Container(items=[dict, {"key": "value"}, list])

        serialized = PolymorphicSerde._to_json(container)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert deserialized.items[0] is dict
        assert deserialized.items[1] == {"key": "value"}
        assert deserialized.items[2] is list

    def test_class_reference_to_pydantic_model(self):
        """Test storing reference to a Pydantic model class."""
        from tests.conftest import Factory, Person

        factory = Factory(model_class=Person)

        serialized = PolymorphicSerde._to_json(factory)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert deserialized.model_class is Person
        # Verify we can instantiate from the reference
        instance = deserialized.model_class(name="Test", age=25)
        assert isinstance(instance, Person)
