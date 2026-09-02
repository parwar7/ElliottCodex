"""Small standard-library validator for the protected schema's used keywords."""

from __future__ import annotations

import json
import math
from pathlib import Path
import re
from typing import Any

from .brain import DEFAULT_PROTECTED_ROOT, BrainIntegrityError, load_required_json


PROTECTED_SCHEMA_PATH = "schemas/ANALYSIS_OUTPUT_SCHEMA.json"
SUPPORTED_DIALECT = "https://json-schema.org/draft/2020-12/schema"
SUPPORTED_VALIDATION_KEYWORDS = frozenset(
    {
        "additionalProperties",
        "const",
        "enum",
        "items",
        "minItems",
        "minLength",
        "pattern",
        "properties",
        "required",
        "type",
        "uniqueItems",
    }
)
SUPPORTED_METADATA_KEYWORDS = frozenset({"$id", "title"})
SUPPORTED_SCHEMA_TYPES = frozenset(
    {"object", "array", "string", "number", "integer", "boolean", "null"}
)


class ProtectedSchemaValidationError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        super().__init__("Protected schema validation failed: " + "; ".join(errors))
        self.errors = tuple(errors)


class UnsupportedProtectedSchemaError(ValueError):
    """Raised before instance validation when the schema is not fully understood."""


def load_protected_output_schema(
    protected_root: str | Path = DEFAULT_PROTECTED_ROOT,
) -> dict[str, Any]:
    schema = load_required_json(PROTECTED_SCHEMA_PATH, protected_root)
    assert_supported_schema(schema)
    return schema


def assert_supported_schema(schema: dict[str, Any]) -> None:
    """Fail closed unless every schema construct has explicit local handling."""
    dialect = schema.get("$schema")
    if dialect != SUPPORTED_DIALECT:
        raise UnsupportedProtectedSchemaError(
            f"Unsupported or missing JSON Schema dialect: {dialect!r}"
        )
    _assert_supported_node(schema, "$")


def _assert_supported_node(schema: dict[str, Any], path: str) -> None:
    if not isinstance(schema, dict):
        raise UnsupportedProtectedSchemaError(f"{path}: schema node must be an object")

    recognized = SUPPORTED_VALIDATION_KEYWORDS | SUPPORTED_METADATA_KEYWORDS | {"$schema"}
    unknown = sorted(set(schema) - recognized)
    if unknown:
        raise UnsupportedProtectedSchemaError(
            f"{path}: unsupported schema keyword(s): {', '.join(unknown)}"
        )

    if "$schema" in schema and schema["$schema"] != SUPPORTED_DIALECT:
        raise UnsupportedProtectedSchemaError(
            f"{path}: unsupported JSON Schema dialect {schema['$schema']!r}"
        )
    if "$id" in schema and not isinstance(schema["$id"], str):
        raise UnsupportedProtectedSchemaError(f"{path}: $id must be a string")
    if "title" in schema and not isinstance(schema["title"], str):
        raise UnsupportedProtectedSchemaError(f"{path}: title must be a string")

    if "type" in schema:
        types = [schema["type"]] if isinstance(schema["type"], str) else schema["type"]
        if (
            not isinstance(types, list)
            or not types
            or not all(isinstance(item, str) and item in SUPPORTED_SCHEMA_TYPES for item in types)
        ):
            raise UnsupportedProtectedSchemaError(f"{path}: unsupported type declaration")
    if "required" in schema and (
        not isinstance(schema["required"], list)
        or not all(isinstance(item, str) for item in schema["required"])
    ):
        raise UnsupportedProtectedSchemaError(f"{path}: required must be an array of strings")
    if "properties" in schema:
        properties = schema["properties"]
        if not isinstance(properties, dict):
            raise UnsupportedProtectedSchemaError(f"{path}: properties must be an object")
        for name, child in properties.items():
            if not isinstance(name, str):
                raise UnsupportedProtectedSchemaError(f"{path}: property names must be strings")
            _assert_supported_node(child, f"{path}.properties[{name!r}]")
    if "additionalProperties" in schema and not isinstance(
        schema["additionalProperties"], bool
    ):
        raise UnsupportedProtectedSchemaError(
            f"{path}: only boolean additionalProperties is supported"
        )
    if "items" in schema:
        if not isinstance(schema["items"], dict):
            raise UnsupportedProtectedSchemaError(f"{path}: items must be one schema object")
        _assert_supported_node(schema["items"], f"{path}.items")
    if "enum" in schema and not isinstance(schema["enum"], list):
        raise UnsupportedProtectedSchemaError(f"{path}: enum must be an array")
    for keyword in ("minItems", "minLength"):
        if keyword in schema and (
            not isinstance(schema[keyword], int)
            or isinstance(schema[keyword], bool)
            or schema[keyword] < 0
        ):
            raise UnsupportedProtectedSchemaError(
                f"{path}: {keyword} must be a non-negative integer"
            )
    if "pattern" in schema and not isinstance(schema["pattern"], str):
        raise UnsupportedProtectedSchemaError(f"{path}: pattern must be a string")
    if "uniqueItems" in schema and not isinstance(schema["uniqueItems"], bool):
        raise UnsupportedProtectedSchemaError(f"{path}: uniqueItems must be boolean")


def supported_count_ranks(schema: dict[str, Any]) -> tuple[str, ...]:
    try:
        values = schema["properties"]["counts"]["items"]["properties"]["rank"]["enum"]
    except (KeyError, TypeError) as exc:
        raise BrainIntegrityError("Protected schema does not define counts[].rank enum.") from exc
    if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
        raise BrainIntegrityError("Protected counts[].rank enum is malformed.")
    return tuple(values)


def validate_instance(instance: Any, schema: dict[str, Any]) -> list[str]:
    assert_supported_schema(schema)
    errors: list[str] = []
    _validate(instance, schema, "$", errors)
    return errors


def assert_valid(instance: Any, schema: dict[str, Any]) -> None:
    errors = validate_instance(instance, schema)
    if errors:
        raise ProtectedSchemaValidationError(errors)


def _matches_type(value: Any, expected: str) -> bool:
    return {
        "object": lambda: isinstance(value, dict),
        "array": lambda: isinstance(value, list),
        "string": lambda: isinstance(value, str),
        "number": lambda: isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value),
        "integer": lambda: isinstance(value, int) and not isinstance(value, bool),
        "boolean": lambda: isinstance(value, bool),
        "null": lambda: value is None,
    }.get(expected, lambda: False)()


def _validate(value: Any, schema: dict[str, Any], path: str, errors: list[str]) -> None:
    expected_type = schema.get("type")
    if expected_type is not None:
        types = [expected_type] if isinstance(expected_type, str) else expected_type
        if not isinstance(types, list) or not any(_matches_type(value, item) for item in types):
            errors.append(f"{path}: expected type {expected_type!r}")
            return

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value {value!r} is not in enum")

    if isinstance(value, dict):
        required = schema.get("required", [])
        for name in required:
            if name not in value:
                errors.append(f"{path}: missing required property {name!r}")
        properties = schema.get("properties", {})
        for name, child in value.items():
            if name in properties:
                _validate(child, properties[name], f"{path}.{name}", errors)
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: additional property {name!r} is not allowed")

    if isinstance(value, list):
        minimum = schema.get("minItems")
        if isinstance(minimum, int) and len(value) < minimum:
            errors.append(f"{path}: requires at least {minimum} items")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate(item, item_schema, f"{path}[{index}]", errors)
        if schema.get("uniqueItems") is True:
            canonical = [json.dumps(item, sort_keys=True, separators=(",", ":")) for item in value]
            if len(canonical) != len(set(canonical)):
                errors.append(f"{path}: items must be unique")

    if isinstance(value, str):
        minimum = schema.get("minLength")
        if isinstance(minimum, int) and len(value) < minimum:
            errors.append(f"{path}: string is shorter than {minimum}")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, value) is None:
            errors.append(f"{path}: string does not match {pattern!r}")
