"""Tests for version tracking and compatibility checking."""

import pytest
import warnings
from unittest.mock import patch
from polyserde import PolymorphicSerde
from tests.conftest import Person


class TestVersionSerialization:
    """Test that version info is properly included in serialization."""

    def test_dump_without_version(self, simple_person):
        result = PolymorphicSerde.dump(simple_person)

        assert "__class__" in result
        assert "__lib__" not in result
        assert "__version__" not in result

    def test_dump_with_lib_only(self, simple_person):
        result = PolymorphicSerde.dump(simple_person, lib="mylib")

        assert result["__lib__"] == "mylib"
        assert "__version__" not in result

    def test_dump_with_version_only(self, simple_person):
        result = PolymorphicSerde.dump(simple_person, version="1.2.3")

        assert result["__version__"] == "1.2.3"
        assert "__lib__" not in result

    def test_dump_with_lib_and_version(self, simple_person):
        result = PolymorphicSerde.dump(simple_person, lib="mylib", version="1.2.3")

        assert result["__lib__"] == "mylib"
        assert result["__version__"] == "1.2.3"

    def test_dump_preserves_data(self, simple_person):
        """Ensure version metadata doesn't interfere with data."""
        result = PolymorphicSerde.dump(simple_person, lib="test", version="1.0.0")

        assert result["name"] == "Alice"
        assert result["age"] == 30
        assert result["__class__"] == "tests.conftest.Person"


class TestVersionDeserialization:
    """Test that version info is properly handled during deserialization."""

    def test_load_without_version(self):
        data = {
            "__class__": "tests.conftest.Person",
            "name": "Bob",
            "age": 25
        }
        result = PolymorphicSerde.load(data)

        assert isinstance(result, Person)
        assert result.name == "Bob"

    def test_load_with_version_attaches_metadata(self):
        data = {
            "__class__": "tests.conftest.Person",
            "__lib__": "mylib",
            "__version__": "1.2.3",
            "name": "Bob",
            "age": 25
        }
        result = PolymorphicSerde.load(data)

        assert hasattr(result, "__serde_lib__")
        assert hasattr(result, "__serde_version__")
        assert result.__serde_lib__ == "mylib"
        assert result.__serde_version__ == "1.2.3"

    def test_load_removes_version_from_data(self):
        """Ensure __lib__ and __version__ are not passed to model_validate."""
        data = {
            "__class__": "tests.conftest.Person",
            "__lib__": "mylib",
            "__version__": "1.2.3",
            "name": "Charlie",
            "age": 30
        }
        result = PolymorphicSerde.load(data)

        # Should not raise validation error about unknown fields
        assert result.name == "Charlie"


class TestVersionCompatibilityChecking:
    """Test semantic version compatibility warnings."""

    @patch('importlib.metadata.version')
    def test_matching_versions_no_warning(self, mock_version, simple_person):
        """Same version should not produce warnings."""
        mock_version.return_value = "1.2.3"

        data = PolymorphicSerde.dump(simple_person, lib="testlib", version="1.2.3")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            PolymorphicSerde.load(data)

            # No warnings should be raised
            assert len(w) == 0

    @patch('importlib.metadata.version')
    def test_patch_version_difference_no_warning(self, mock_version, simple_person):
        """Patch version differences should not warn."""
        mock_version.return_value = "1.2.4"

        data = PolymorphicSerde.dump(simple_person, lib="testlib", version="1.2.3")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            PolymorphicSerde.load(data)

            # No warnings for patch differences
            assert len(w) == 0

    @patch('importlib.metadata.version')
    def test_minor_version_difference_warns(self, mock_version, simple_person):
        """Minor version differences should produce warning."""
        mock_version.return_value = "1.3.0"

        data = PolymorphicSerde.dump(simple_person, lib="testlib", version="1.2.0")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            PolymorphicSerde.load(data)

            assert len(w) == 1
            assert "Minor version difference" in str(w[0].message)
            assert "testlib" in str(w[0].message)

    @patch('importlib.metadata.version')
    def test_major_version_difference_warns(self, mock_version, simple_person):
        """Major version differences should produce strong warning."""
        mock_version.return_value = "2.0.0"

        data = PolymorphicSerde.dump(simple_person, lib="testlib", version="1.2.3")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            PolymorphicSerde.load(data)

            assert len(w) == 1
            assert "Major version mismatch" in str(w[0].message)
            assert "incompatible" in str(w[0].message)

    @patch('importlib.metadata.version')
    def test_library_not_found_warns(self, mock_version, simple_person):
        """Missing library should produce warning."""
        from importlib.metadata import PackageNotFoundError
        mock_version.side_effect = PackageNotFoundError()

        data = PolymorphicSerde.dump(simple_person, lib="nonexistent", version="1.0.0")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            PolymorphicSerde.load(data)

            assert len(w) == 1
            assert "not found" in str(w[0].message)
            assert "nonexistent" in str(w[0].message)


class TestNonSemanticVersions:
    """Test handling of non-semantic version strings."""

    @patch('importlib.metadata.version')
    def test_non_semantic_version_exact_match(self, mock_version, simple_person):
        """Exact match of non-semantic versions should not warn."""
        mock_version.return_value = "custom-v1"

        data = PolymorphicSerde.dump(simple_person, lib="testlib", version="custom-v1")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            PolymorphicSerde.load(data)

            assert len(w) == 0

    @patch('importlib.metadata.version')
    def test_non_semantic_version_mismatch(self, mock_version, simple_person):
        """Non-semantic version mismatch should produce generic warning."""
        mock_version.return_value = "custom-v2"

        data = PolymorphicSerde.dump(simple_person, lib="testlib", version="custom-v1")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            PolymorphicSerde.load(data)

            assert len(w) == 1
            assert "Version mismatch" in str(w[0].message)


class TestVersionRoundtrip:
    """Test complete roundtrip with version tracking."""

    @patch('importlib.metadata.version')
    def test_full_roundtrip_with_version(self, mock_version, simple_person):
        """Test complete dump/load cycle with version checking."""
        mock_version.return_value = "1.2.3"

        # Dump with version
        dumped = PolymorphicSerde.dump(simple_person, lib="testlib", version="1.2.3")

        # Load and verify
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            loaded = PolymorphicSerde.load(dumped)

            assert len(w) == 0  # No warnings
            assert loaded.name == simple_person.name
            assert loaded.age == simple_person.age
            assert loaded.__serde_lib__ == "testlib"
            assert loaded.__serde_version__ == "1.2.3"

    def test_version_metadata_not_in_original_data(self):
        """Ensure original data dict is not mutated."""
        data = {
            "__class__": "tests.conftest.Person",
            "__lib__": "mylib",
            "__version__": "1.0.0",
            "name": "Test",
            "age": 20
        }

        # Make a copy to verify non-mutation
        original_keys = set(data.keys())

        PolymorphicSerde.load(data)

        # Original data should still have version keys
        assert set(data.keys()) == original_keys
