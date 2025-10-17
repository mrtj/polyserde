"""Pytest configuration and shared fixtures for polyserde tests."""

import pytest
from enum import Enum
from pydantic import BaseModel
from typing import Optional


# Test fixtures: Enums
class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


# Test fixtures: Simple Pydantic models
class Address(BaseModel):
    street: str
    city: str
    zipcode: str


class Person(BaseModel):
    name: str
    age: int
    email: Optional[str] = None


# Test fixtures: Polymorphic models (base + subclasses)
class Animal(BaseModel):
    name: str
    species: str


class Cat(Animal):
    lives_left: int = 9
    favorite_toy: Optional[str] = None


class Dog(Animal):
    breed: str
    is_good_boy: bool = True


class Bird(Animal):
    can_fly: bool = True
    wingspan_cm: Optional[float] = None


# Test fixtures: Complex nested models
class Zoo(BaseModel):
    location: str
    animals: list[Animal]
    staff: list[Person]
    metadata: dict[str, str] = {}


class Configuration(BaseModel):
    name: str
    priority: Priority
    colors: list[Color]
    settings: dict[str, int]
    handler_class: type = dict


# Additional test models for complex scenarios
class Company(BaseModel):
    name: str
    ceo: Person


class Team(BaseModel):
    name: str
    members: list[Person]


class Registry(BaseModel):
    string_handler: type
    number_handler: type
    collection_handler: type


class Container(BaseModel):
    items: list


class Factory(BaseModel):
    model_class: type


class Settings(BaseModel):
    theme: dict[str, Color]


class Mapping(BaseModel):
    color_codes: dict[Color, str]


class IndexedData(BaseModel):
    items: dict[int, str]


# Recursive model
class Node(BaseModel):
    value: int
    child: Optional['Node'] = None


# Enum with duplicates for testing
class Status(Enum):
    PENDING = 1
    WAITING = 1  # Alias
    ACTIVE = 2


class Palette(BaseModel):
    color_groups: list[list[Color]]


@pytest.fixture
def simple_person():
    return Person(name="Alice", age=30, email="alice@example.com")


@pytest.fixture
def simple_address():
    return Address(street="123 Main St", city="Springfield", zipcode="12345")


@pytest.fixture
def polymorphic_animals():
    return [
        Cat(name="Whiskers", species="Felis catus", lives_left=7, favorite_toy="yarn"),
        Dog(name="Rex", species="Canis familiaris", breed="Labrador"),
        Bird(name="Tweety", species="Serinus canaria", wingspan_cm=15.5),
    ]


@pytest.fixture
def complex_zoo(polymorphic_animals):
    return Zoo(
        location="Berlin Zoo",
        animals=polymorphic_animals,
        staff=[
            Person(name="Bob", age=45, email="bob@zoo.com"),
            Person(name="Carol", age=32),
        ],
        metadata={"established": "1844", "size_hectares": "33"},
    )


@pytest.fixture
def config_with_enums():
    return Configuration(
        name="test_config",
        priority=Priority.HIGH,
        colors=[Color.RED, Color.BLUE],
        settings={"timeout": 30, "retries": 3},
        handler_class=list,
    )
