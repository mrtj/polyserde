"""Tests for polymorphic model handling - the core feature of polyserde."""

import pytest
from polyserde import PolymorphicSerde
from tests.conftest import Animal, Cat, Dog, Bird, Zoo


class TestPolymorphicSerialization:
    """Test that subclass types are preserved during serialization."""

    def test_serialize_cat_preserves_type(self):
        cat = Cat(name="Whiskers", species="Felis catus", lives_left=7)
        result = PolymorphicSerde._to_json(cat)

        assert result["__class__"] == "tests.conftest.Cat"
        assert result["name"] == "Whiskers"
        assert result["lives_left"] == 7

    def test_serialize_dog_preserves_type(self):
        dog = Dog(name="Rex", species="Canis familiaris", breed="Labrador")
        result = PolymorphicSerde._to_json(dog)

        assert result["__class__"] == "tests.conftest.Dog"
        assert result["breed"] == "Labrador"
        assert result["is_good_boy"] is True

    def test_serialize_bird_preserves_type(self):
        bird = Bird(name="Tweety", species="Serinus canaria", wingspan_cm=15.5)
        result = PolymorphicSerde._to_json(bird)

        assert result["__class__"] == "tests.conftest.Bird"
        assert result["wingspan_cm"] == 15.5
        assert result["can_fly"] is True


class TestPolymorphicDeserialization:
    """Test that correct subclass types are restored during deserialization."""

    def test_deserialize_cat(self):
        data = {
            "__class__": "tests.conftest.Cat",
            "name": "Mittens",
            "species": "Felis catus",
            "lives_left": 9,
            "favorite_toy": "ball"
        }
        result = PolymorphicSerde._from_json(data)

        assert isinstance(result, Cat)
        assert type(result) is Cat  # Exact type match
        assert result.name == "Mittens"
        assert result.lives_left == 9
        assert result.favorite_toy == "ball"

    def test_deserialize_dog(self):
        data = {
            "__class__": "tests.conftest.Dog",
            "name": "Buddy",
            "species": "Canis familiaris",
            "breed": "Golden Retriever",
            "is_good_boy": True
        }
        result = PolymorphicSerde._from_json(data)

        assert isinstance(result, Dog)
        assert type(result) is Dog
        assert result.breed == "Golden Retriever"

    def test_deserialize_bird(self):
        data = {
            "__class__": "tests.conftest.Bird",
            "name": "Polly",
            "species": "Psittacus erithacus",
            "can_fly": False,
            "wingspan_cm": 30.0
        }
        result = PolymorphicSerde._from_json(data)

        assert isinstance(result, Bird)
        assert type(result) is Bird
        assert result.can_fly is False


class TestPolymorphicLists:
    """Test lists containing mixed subclass types."""

    def test_serialize_mixed_animal_list(self, polymorphic_animals):
        result = PolymorphicSerde._to_json(polymorphic_animals)

        assert len(result) == 3
        assert result[0]["__class__"] == "tests.conftest.Cat"
        assert result[1]["__class__"] == "tests.conftest.Dog"
        assert result[2]["__class__"] == "tests.conftest.Bird"

    def test_deserialize_mixed_animal_list(self):
        data = [
            {"__class__": "tests.conftest.Cat", "name": "Whiskers", "species": "Felis catus", "lives_left": 7},
            {"__class__": "tests.conftest.Dog", "name": "Rex", "species": "Canis familiaris", "breed": "Labrador"},
            {"__class__": "tests.conftest.Bird", "name": "Tweety", "species": "Serinus canaria", "can_fly": True},
        ]
        result = PolymorphicSerde._from_json(data)

        assert len(result) == 3
        assert type(result[0]) is Cat
        assert type(result[1]) is Dog
        assert type(result[2]) is Bird

    def test_roundtrip_polymorphic_list(self, polymorphic_animals):
        """Critical test: ensure exact types are preserved through roundtrip."""
        serialized = PolymorphicSerde._to_json(polymorphic_animals)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert len(deserialized) == 3

        # Verify exact types
        assert type(deserialized[0]) is Cat
        assert type(deserialized[1]) is Dog
        assert type(deserialized[2]) is Bird

        # Verify all are still Animals (polymorphism works)
        assert all(isinstance(animal, Animal) for animal in deserialized)

        # Verify data integrity
        assert deserialized[0].name == "Whiskers"
        assert deserialized[0].lives_left == 7
        assert deserialized[1].breed == "Labrador"
        assert deserialized[2].wingspan_cm == 15.5


class TestPolymorphicInContainers:
    """Test polymorphic models nested in complex structures."""

    def test_zoo_with_mixed_animals(self, complex_zoo):
        """Test a complex model containing polymorphic lists."""
        serialized = PolymorphicSerde._to_json(complex_zoo)

        assert serialized["location"] == "Berlin Zoo"
        assert len(serialized["animals"]) == 3
        assert serialized["animals"][0]["__class__"] == "tests.conftest.Cat"
        assert serialized["animals"][1]["__class__"] == "tests.conftest.Dog"

    def test_roundtrip_zoo(self, complex_zoo):
        """Full roundtrip test of complex polymorphic structure."""
        serialized = PolymorphicSerde._to_json(complex_zoo)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert isinstance(deserialized, Zoo)
        assert deserialized.location == "Berlin Zoo"

        # Verify polymorphic animals
        assert len(deserialized.animals) == 3
        assert type(deserialized.animals[0]) is Cat
        assert type(deserialized.animals[1]) is Dog
        assert type(deserialized.animals[2]) is Bird

        # Verify staff (non-polymorphic but still Pydantic)
        assert len(deserialized.staff) == 2
        assert deserialized.staff[0].name == "Bob"
        assert deserialized.staff[1].email is None

        # Verify metadata dict
        assert deserialized.metadata["established"] == "1844"


class TestPolymorphicEdgeCases:
    """Edge cases for polymorphic handling."""

    def test_base_class_serialization(self):
        """Test that base class instances work too."""
        animal = Animal(name="Generic", species="Unknown")
        serialized = PolymorphicSerde._to_json(animal)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert type(deserialized) is Animal
        assert deserialized.name == "Generic"

    def test_deeply_nested_polymorphic(self):
        """Test polymorphic models nested multiple levels deep."""
        from pydantic import BaseModel

        class Habitat(BaseModel):
            name: str
            residents: list[Animal]

        class Park(BaseModel):
            habitats: list[Habitat]

        park = Park(
            habitats=[
                Habitat(name="Savanna", residents=[
                    Dog(name="Wild Dog", species="Lycaon pictus", breed="African Wild Dog")
                ]),
                Habitat(name="Aviary", residents=[
                    Bird(name="Eagle", species="Aquila chrysaetos", wingspan_cm=200.0)
                ])
            ]
        )

        serialized = PolymorphicSerde._to_json(park)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert len(deserialized.habitats) == 2
        assert type(deserialized.habitats[0].residents[0]) is Dog
        assert type(deserialized.habitats[1].residents[0]) is Bird
