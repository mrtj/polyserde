"""Integration tests for complex, real-world scenarios."""

import pytest
from polyserde import PolymorphicSerde
from pydantic import BaseModel
from tests.conftest import (Zoo, Person, Cat, Dog, Bird, Color, Priority, Preprocessor, Normalizer, Tokenizer, Model, Transformer, CNN, Pipeline, Converter, PDFConverter, DOCXConverter, OutputFormat, MarkdownOutput, JSONOutput, DocumentPipeline, Item, Book, DVD, NestedContainer, Box, Shelf, Storage, Config, GraphNode, Graph)
from typing import Optional


class TestRealWorldScenarios:
    """Test realistic, complex use cases."""

    def test_complete_zoo_roundtrip(self, complex_zoo):
        """Test the example from the README."""
        serialized = PolymorphicSerde.dump(
            complex_zoo,
            lib="zoolib",
            version="1.2.3"
        )

        deserialized = PolymorphicSerde.load(serialized)

        assert isinstance(deserialized, Zoo)
        assert deserialized.location == "Berlin Zoo"
        assert len(deserialized.animals) == 3
        assert type(deserialized.animals[0]) is Cat
        assert type(deserialized.animals[1]) is Dog
        assert type(deserialized.animals[2]) is Bird
        assert len(deserialized.staff) == 2
        assert deserialized.__serde_lib__ == "zoolib"
        assert deserialized.__serde_version__ == "1.2.3"

    def test_ml_pipeline_config(self):
        """Simulate ML pipeline configuration."""

        pipeline = Pipeline(
            name="text_classifier",
            preprocessors=[
                Tokenizer(name="bert_tokenizer", vocab_size=30000, max_length=512),
                Normalizer(name="feature_norm", mean=0.0, std=1.0),
            ],
            model=Transformer(name="bert_base", layers=12, attention_heads=12),
            batch_size=32
        )

        # Serialize
        serialized = PolymorphicSerde.dump(pipeline, lib="ml_framework", version="2.0.0")

        # Deserialize
        loaded = PolymorphicSerde.load(serialized)

        assert loaded.name == "text_classifier"
        assert len(loaded.preprocessors) == 2
        assert type(loaded.preprocessors[0]) is Tokenizer
        assert type(loaded.preprocessors[1]) is Normalizer
        assert type(loaded.model) is Transformer
        assert loaded.model.layers == 12

    def test_document_processing_config(self):
        """Simulate document processing configuration."""

        pipeline = DocumentPipeline(
            converters={
                "pdf": PDFConverter(name="pdf_conv", dpi=600),
                "docx": DOCXConverter(name="docx_conv", preserve_formatting=False),
            },
            output=MarkdownOutput(format_type="markdown", include_toc=True),
            priority=Priority.HIGH
        )

        serialized = PolymorphicSerde.dump(pipeline, lib="docling", version="0.14.0")
        loaded = PolymorphicSerde.load(serialized)

        assert isinstance(loaded.converters["pdf"], PDFConverter)
        assert loaded.converters["pdf"].dpi == 600
        assert isinstance(loaded.output, MarkdownOutput)
        assert loaded.output.include_toc is True
        assert loaded.priority == Priority.HIGH


class TestNestedPolymorphism:
    """Test deeply nested polymorphic structures."""

    def test_nested_polymorphic_collections(self):
        """Multiple levels of polymorphic nesting."""

        storage = Storage(
            containers=[
                Box(
                    label="Media Box",
                    fragile=True,
                    items=[
                        DVD(name="Movie 1", duration_minutes=120),
                        DVD(name="Movie 2", duration_minutes=95),
                    ]
                ),
                Shelf(
                    label="Bookshelf",
                    level=2,
                    items=[
                        Book(name="Book 1", author="Author A", pages=300),
                        Book(name="Book 2", author="Author B", pages=450),
                    ]
                ),
            ]
        )

        serialized = PolymorphicSerde._to_json(storage)
        deserialized = PolymorphicSerde._from_json(serialized)

        # Verify container types
        assert type(deserialized.containers[0]) is Box
        assert type(deserialized.containers[1]) is Shelf

        # Verify item types
        assert type(deserialized.containers[0].items[0]) is DVD
        assert type(deserialized.containers[1].items[0]) is Book

        # Verify data
        assert deserialized.containers[0].fragile is True
        assert deserialized.containers[1].items[0].author == "Author A"


class TestComplexDataStructures:
    """Test complex combinations of features."""

    def test_kitchen_sink(self):
        """Test combining all features: models, enums, class refs, complex dicts."""

        config = Config(
            name="complex_config",
            priority_map={
                Color.RED: Priority.HIGH,
                Color.GREEN: Priority.LOW,
            },
            handlers={
                "dict": dict,
                "list": list,
            },
            animals=[
                Cat(name="Cat1", species="Felis", lives_left=9),
                Cat(name="Cat2", species="Felis", lives_left=7),
            ],
            metadata={
                1: "first",
                2: "second",
            },
            staff=Person(name="Manager", age=40, email="mgr@example.com")
        )

        serialized = PolymorphicSerde.dump(config, lib="testlib", version="1.0.0")
        loaded = PolymorphicSerde.load(serialized)

        # Verify all features work together
        assert loaded.priority_map[Color.RED] == Priority.HIGH
        assert loaded.handlers["dict"] is dict
        assert type(loaded.animals[0]) is Cat
        assert loaded.metadata[1] == "first"
        assert isinstance(loaded.staff, Person)

    def test_graph_like_structure(self):
        """Test a graph-like structure (non-circular)."""

        graph = Graph(
            nodes={
                1: GraphNode(id=1, value="A", neighbors=[2, 3]),
                2: GraphNode(id=2, value="B", neighbors=[1]),
                3: GraphNode(id=3, value="C", neighbors=[1, 2]),
            }
        )

        serialized = PolymorphicSerde._to_json(graph)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert len(deserialized.nodes) == 3
        assert deserialized.nodes[1].value == "A"
        assert 2 in deserialized.nodes[1].neighbors


class TestListsOfLists:
    """Test various nested list scenarios."""

    def test_list_of_model_lists(self):
        groups = [
            [Person(name="A", age=20), Person(name="B", age=21)],
            [Person(name="C", age=30)],
        ]

        serialized = PolymorphicSerde._to_json(groups)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert len(deserialized) == 2
        assert len(deserialized[0]) == 2
        assert isinstance(deserialized[0][0], Person)
        assert deserialized[0][0].name == "A"

    def test_matrix_of_primitives(self):
        matrix = [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
        ]

        serialized = PolymorphicSerde._to_json(matrix)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert deserialized == matrix


class TestDictOfDicts:
    """Test nested dictionary scenarios."""

    def test_dict_of_model_dicts(self):
        data = {
            "team1": {
                "alice": Person(name="Alice", age=30),
                "bob": Person(name="Bob", age=25),
            },
            "team2": {
                "charlie": Person(name="Charlie", age=35),
            }
        }

        serialized = PolymorphicSerde._to_json(data)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert isinstance(deserialized["team1"]["alice"], Person)
        assert deserialized["team1"]["alice"].name == "Alice"
        assert deserialized["team2"]["charlie"].age == 35

    def test_nested_config_dict(self):
        """Configuration-style nested dictionaries."""
        config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "credentials": {
                    "user": "admin",
                    "password": "secret"
                }
            },
            "cache": {
                "enabled": True,
                "ttl": 300
            }
        }

        serialized = PolymorphicSerde._to_json(config)
        deserialized = PolymorphicSerde._from_json(serialized)

        assert deserialized["database"]["credentials"]["user"] == "admin"
        assert deserialized["cache"]["ttl"] == 300
