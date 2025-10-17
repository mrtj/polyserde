"""Tests for Pydantic model serialization and deserialization."""

import pytest
from polyserde import PolymorphicSerde
from tests.conftest import Person, Address


class TestSimplePydanticModels:
    """Test basic Pydantic model serialization."""

    def test_serialize_simple_model(self, simple_person):
        result = PolymorphicSerde._to_json(simple_person)

        assert isinstance(result, dict)
        assert result["name"] == "Alice"
        assert result["age"] == 30
        assert result["email"] == "alice@example.com"
        assert result["__class__"] == "tests.conftest.Person"

    def test_deserialize_simple_model(self):
        data = {
            "__class__": "tests.conftest.Person",
            "name": "Bob",
            "age": 25,
            "email": "bob@test.com"
        }
        result = PolymorphicSerde._from_json(data)

        assert isinstance(result, Person)
        assert result.name == "Bob"
        assert result.age == 25
        assert result.email == "bob@test.com"

    def test_roundtrip_simple_model(self, simple_person):
        serialized = PolymorphicSerde._to_json(simple_person)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert isinstance(deserialized, Person)
        assert deserialized.name == simple_person.name
        assert deserialized.age == simple_person.age
        assert deserialized.email == simple_person.email

    def test_model_with_optional_none(self):
        person = Person(name="Charlie", age=40)  # No email
        serialized = PolymorphicSerde._to_json(person)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert isinstance(deserialized, Person)
        assert deserialized.name == "Charlie"
        assert deserialized.age == 40
        assert deserialized.email is None

    def test_serialize_address(self, simple_address):
        result = PolymorphicSerde._to_json(simple_address)

        assert result["street"] == "123 Main St"
        assert result["city"] == "Springfield"
        assert result["zipcode"] == "12345"
        assert result["__class__"] == "tests.conftest.Address"

    def test_roundtrip_address(self, simple_address):
        serialized = PolymorphicSerde._to_json(simple_address)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert isinstance(deserialized, Address)
        assert deserialized.street == simple_address.street
        assert deserialized.city == simple_address.city
        assert deserialized.zipcode == simple_address.zipcode


class TestPydanticModelLists:
    """Test lists of Pydantic models."""

    def test_serialize_list_of_models(self):
        people = [
            Person(name="Alice", age=30),
            Person(name="Bob", age=25, email="bob@test.com"),
        ]
        result = PolymorphicSerde._to_json(people)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"
        assert all("__class__" in item for item in result)

    def test_deserialize_list_of_models(self):
        data = [
            {"__class__": "tests.conftest.Person", "name": "Alice", "age": 30},
            {"__class__": "tests.conftest.Person", "name": "Bob", "age": 25},
        ]
        result = PolymorphicSerde._from_json(data)

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(p, Person) for p in result)
        assert result[0].name == "Alice"
        assert result[1].name == "Bob"

    def test_roundtrip_list_of_models(self):
        people = [
            Person(name="Alice", age=30, email="alice@test.com"),
            Person(name="Bob", age=25),
        ]
        serialized = PolymorphicSerde._to_json(people)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert len(deserialized) == 2
        assert deserialized[0].name == "Alice"
        assert deserialized[0].email == "alice@test.com"
        assert deserialized[1].name == "Bob"
        assert deserialized[1].email is None


class TestNestedPydanticModels:
    """Test Pydantic models containing other Pydantic models."""

    def test_serialize_model_with_nested_model(self):
        from tests.conftest import Company

        company = Company(
            name="TechCorp",
            ceo=Person(name="Jane", age=45, email="jane@techcorp.com")
        )

        result = PolymorphicSerde._to_json(company)

        assert result["name"] == "TechCorp"
        assert isinstance(result["ceo"], dict)
        assert result["ceo"]["name"] == "Jane"
        assert result["ceo"]["__class__"] == "tests.conftest.Person"

    def test_roundtrip_nested_model(self):
        from tests.conftest import Team

        team = Team(
            name="Engineering",
            members=[
                Person(name="Alice", age=30),
                Person(name="Bob", age=25, email="bob@test.com"),
            ]
        )

        serialized = PolymorphicSerde._to_json(team)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert isinstance(deserialized, Team)
        assert deserialized.name == "Engineering"
        assert len(deserialized.members) == 2
        assert all(isinstance(m, Person) for m in deserialized.members)
