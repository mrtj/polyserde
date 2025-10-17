# Polyserde

**Generic polymorphic serializer/deserializer for Pydantic models and complex Python object graphs.**

`polyserde` is a lightweight utility for serializing and deserializing **nested, polymorphic configuration objects** — including **Pydantic models**, **enums**, **class references**, and **dictionaries with non-string keys** — into portable, self-describing JSON.

It’s ideal for libraries and applications that:

* Use configuration graphs composed of subclassed Pydantic models,
* Need version-safe persistence of structured data (e.g. ML pipelines, document converters, etc.),
* Require **semantic version compatibility checks** when reloading saved configs.

---

## Features

* Full polymorphic support — preserves subclass types automatically
* Nested object graphs — handles lists, dicts, enums, and class references
* Library-agnostic — works with any Pydantic 2.x models
* Version tracking — stores the originating library name and version
* Semantic version checking — warns if the loaded config may be incompatible
* Portable JSON — produces human-readable, self-describing files
* Zero dependencies beyond `pydantic` and `packaging`

---

## Installation

```bash
pip install polyserde
```

Requires **Python ≥ 3.9** and **Pydantic ≥ 2.0**.

---

## Quick Start

Below is a complete usage example. Suppose the following classes are defined inside a module called `zoolib`.

```python
# zoolib/__init__.py
from pydantic import BaseModel
from enum import Enum

class Species(Enum):
    CAT = "cat"
    DOG = "dog"

class Animal(BaseModel):
    name: str
    species: Species

class Cat(Animal):
    lives_left: int = 9

class Dog(Animal):
    breed: str
    is_good_boy: bool = True

class Zoo(BaseModel):
    location: str
    animals: list[Animal]
    caretaker_class: type = dict  # just an example class reference
```

Now use `polyserde` to serialize and deserialize the structure:

```python
from zoolib import Zoo, Cat, Dog, Species
from polyserde import PolymorphicSerde

zoo = Zoo(
    location="Berlin",
    animals=[
        Cat(name="Mittens", species=Species.CAT, lives_left=7),
        Dog(name="Rex", species=Species.DOG, breed="Labrador"),
    ]
)

# Serialize to JSON file
PolymorphicSerde.dump(
    zoo,
    fp="zoo_config.json",
    lib="zoolib",
    version="1.2.3",
)

# Deserialize (with version checking)
restored = PolymorphicSerde.load("zoo_config.json")
print(restored)
print(type(restored.animals[0]))
```

**Output:**

```
Zoo(location='Berlin', animals=[Cat(...), Dog(...)], caretaker_class=<class 'dict'>)
<class 'zoolib.Cat'>
```

If the current environment doesn’t have the same library version, `polyserde` emits helpful warnings such as:

```
⚠️ Major version mismatch for zoolib: serialized=1.2.3, installed=2.0.0 (config may be incompatible)
```

---

## How It Works

`PolymorphicSerde` recursively converts complex Python objects into a JSON-safe structure with embedded type metadata:

* Each Pydantic model is tagged with `"__class__": "module.ClassName"`.
* Enums are represented as `"__enum__": "module.EnumClass.MEMBER"`.
* Class references are stored as `"__class_ref__": "module.Class"`.
* Non-string dict keys are safely represented via `{ "__dict__": [{"__key__": ..., "value": ...}, ...]}`.

This makes every JSON file **self-describing** — you can reload it anywhere, and `PolymorphicSerde` will reconstruct the correct objects automatically.

---

## Version Safety

When saving a configuration, you can specify both the **library name** and **version**:

```python
PolymorphicSerde.dump(my_config, "config.json", lib="docling", version="0.14.0")
```

At load time, `polyserde`:

* Looks up the installed version of the library,
* Parses both versions semantically (using [PEP 440](https://peps.python.org/pep-0440/)),
* Emits a warning if major or minor versions differ,
* Falls back to strict equality for non-semantic versions.

Example warning:

```
⚠️ Minor version difference for docling: serialized=0.14.0, installed=0.15.0 (review config compatibility)
```

---

## Design Goals

| Goal         | Description                                      |
| ------------ | ------------------------------------------------ |
| Transparency | Human-readable and inspectable JSON output       |
| Determinism  | Each object restored to the exact original type  |
| Portability  | No runtime scanning or registry lookups required |
| Safety       | Detects version mismatches automatically         |
| Simplicity   | Single-file, dependency-light, production-ready  |

---

## Roadmap

* [ ] Add optional YAML serialization (`ruamel.yaml` / `pyyaml`)
* [ ] Add "strict" mode to raise on incompatible versions
* [ ] Add schema validation helpers for known models
* [ ] Add CLI for quick inspect / roundtrip testing

---

## Contributing

Contributions are welcome!
If you’d like to improve the serializer, add features, or extend compatibility, feel free to open a PR or issue.

1. Fork the repo
2. Create a feature branch
3. Run tests (`pytest`)
4. Submit a PR

---

## Acknowledgments

Inspired by real-world serialization challenges in projects like **Docling**, **FastAPI**, and **LangChain**, where polymorphic configuration graphs are the norm.

`polyserde` brings predictable, portable, and version-safe serialization to any Pydantic-based system.
