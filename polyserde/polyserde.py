from typing import Any, Optional
from enum import Enum
import inspect
import importlib
import importlib.metadata
import warnings

from pydantic import BaseModel
from packaging.version import Version, InvalidVersion


class PolymorphicSerde:
    """
    Generic serializer/deserializer for complex Pydantic 2.x configuration graphs.
    Handles polymorphism, enums, class references, and version compatibility.
    """

    VERSION_KEY = "__version__"
    LIB_KEY = "__lib__"
    CLASS_KEY = "__class__"
    ENUM_KEY = "__enum__"
    CLASS_REF_KEY = "__class_ref__"
    KEY_TAG = "__key__"
    TUPLE_KEY = "__tuple__"

    # ---------------------
    # Public API
    # ---------------------

    @classmethod
    def dump(
        cls,
        obj: Any,
        *,
        lib: Optional[str] = None,
        version: Optional[str] = None,
    ) -> dict:
        """Serialize object to JSON-safe dict, embedding library and version info."""
        data = cls._to_json(obj)
        if lib:
            data[cls.LIB_KEY] = lib
        if version:
            data[cls.VERSION_KEY] = version
        return data

    @classmethod
    def load(cls, data: dict) -> Any:
        """Deserialize and validate version compatibility."""

        # Defensive copy to avoid mutating the original input
        data = dict(data)

        lib_name = data.pop(cls.LIB_KEY, None)
        version_str = data.pop(cls.VERSION_KEY, None)
        obj = cls._from_json(data)

        if lib_name and version_str:
            cls._check_version_compatibility(lib_name, version_str)

        # Attach version info only if the deserialized object can have attributes
        if hasattr(obj, "__dict__"):
            if lib_name:
                setattr(obj, "__serde_lib__", lib_name)
            if version_str:
                setattr(obj, "__serde_version__", version_str)
        else:
            # If the object is not a Pydantic model or similar, just return it
            warnings.warn(
                "Deserialized root is not an object that supports attributes; version metadata not attached."
            )

        return obj


    # ---------------------
    # Version Checking
    # ---------------------

    @staticmethod
    def _check_version_compatibility(lib_name: str, serialized_version: str):
        """Compare serialized vs installed version and emit semantic warnings."""
        try:
            installed_version = importlib.metadata.version(lib_name)
        except importlib.metadata.PackageNotFoundError:
            warnings.warn(
                f"⚠️ Library '{lib_name}' not found; cannot verify version compatibility."
            )
            return

        try:
            v_serialized = Version(serialized_version)
            v_installed = Version(installed_version)
        except InvalidVersion:
            if serialized_version != installed_version:
                warnings.warn(
                    f"⚠️ Version mismatch for {lib_name}: serialized={serialized_version}, "
                    f"installed={installed_version}"
                )
            return

        # Semantic check: warn on major version differences
        if v_serialized.major != v_installed.major:
            warnings.warn(
                f"⚠️ Major version mismatch for {lib_name}: "
                f"serialized={serialized_version}, installed={installed_version} "
                f"(config may be incompatible)"
            )
        elif v_serialized.minor != v_installed.minor:
            warnings.warn(
                f"⚠️ Minor version difference for {lib_name}: "
                f"serialized={serialized_version}, installed={installed_version} "
                f"(review config compatibility)"
            )

    # ---------------------
    # Internal: Serializer
    # ---------------------

    @classmethod
    def _to_json(cls, obj: Any) -> Any:
        if isinstance(obj, BaseModel):
            data = {}
            for k, v in obj.__dict__.items():
                if k.startswith("_"):
                    continue
                data[k] = cls._to_json(v)
            data[cls.CLASS_KEY] = f"{obj.__class__.__module__}.{obj.__class__.__name__}"
            return data

        elif isinstance(obj, Enum):
            return {cls.ENUM_KEY: f"{obj.__class__.__module__}.{obj.__class__.__name__}.{obj.name}"}

        elif inspect.isclass(obj):
            return {cls.CLASS_REF_KEY: f"{obj.__module__}.{obj.__name__}"}

        elif isinstance(obj, dict):
            items = []
            for k, v in obj.items():
                items.append({cls.KEY_TAG: cls._to_json(k), "value": cls._to_json(v)})
            return {"__dict__": items}

        elif isinstance(obj, list):
            return [cls._to_json(v) for v in obj]
        elif isinstance(obj, tuple):
            # Mark tuples so they can be reconstructed (important for dict keys)
            return {cls.TUPLE_KEY: [cls._to_json(v) for v in obj]}

        elif obj is None or isinstance(obj, (str, int, float, bool)):
            return obj

        if hasattr(obj, "__class__") and hasattr(obj.__class__, "__module__"):
            return {cls.CLASS_REF_KEY: f"{obj.__class__.__module__}.{obj.__class__.__name__}"}

        return str(obj)

    # ---------------------
    # Internal: Deserializer
    # ---------------------

    @classmethod
    def _from_json(cls, obj: Any) -> Any:
        if isinstance(obj, dict):
            if cls.ENUM_KEY in obj:
                module, enum_name, member = obj[cls.ENUM_KEY].rsplit(".", 2)
                enum_cls = cls._import_from_path(f"{module}.{enum_name}")
                return enum_cls[member]

            if cls.CLASS_REF_KEY in obj:
                return cls._import_from_path(obj[cls.CLASS_REF_KEY])

            if cls.TUPLE_KEY in obj:
                return tuple(cls._from_json(v) for v in obj[cls.TUPLE_KEY])

            if cls.CLASS_KEY in obj:
                class_path = obj.pop(cls.CLASS_KEY)
                model_cls = cls._import_from_path(class_path)
                data = {k: cls._from_json(v) for k, v in obj.items()}
                return model_cls.model_validate(data)

            if "__dict__" in obj:
                d = {}
                for item in obj["__dict__"]:
                    k = cls._from_json(item[cls.KEY_TAG])
                    v = cls._from_json(item["value"])
                    # Convert list keys to tuples if they can be hashed
                    if isinstance(k, list):
                        try:
                            k = tuple(k)
                        except TypeError:
                            pass  # Keep as list if it contains unhashable items
                    d[k] = v
                return d

            return {cls._from_json(k): cls._from_json(v) for k, v in obj.items()}

        elif isinstance(obj, list):
            return [cls._from_json(v) for v in obj]

        return obj

    # ---------------------
    # Helper
    # ---------------------

    @staticmethod
    def _import_from_path(path: str) -> Any:
        module_name, attr_name = path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        return getattr(module, attr_name)
