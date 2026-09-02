import json
import unittest

import support
from elliott_methodology_kernel.models import CountRank
from elliott_methodology_kernel.schema import (
    ProtectedSchemaValidationError,
    UnsupportedProtectedSchemaError,
    assert_valid,
    load_protected_output_schema,
    supported_count_ranks,
)


class ProtectedSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_protected_output_schema(support.PROTECTED_ROOT)
        cls.example_path = support.PROTECTED_ROOT / "examples" / "EMPTY_ANALYSIS.json"

    def test_protected_example_is_valid(self) -> None:
        example = json.loads(self.example_path.read_text(encoding="utf-8-sig"))
        assert_valid(example, self.schema)

    def test_missing_required_property_is_rejected(self) -> None:
        example = json.loads(self.example_path.read_text(encoding="utf-8-sig"))
        del example["symbol"]
        with self.assertRaises(ProtectedSchemaValidationError):
            assert_valid(example, self.schema)

    def test_invalid_count_rank_is_rejected(self) -> None:
        example = json.loads(self.example_path.read_text(encoding="utf-8-sig"))
        example["counts"][0]["rank"] = "INVENTED"
        with self.assertRaises(ProtectedSchemaValidationError):
            assert_valid(example, self.schema)

    def test_count_rank_enum_exactly_matches_protected_schema(self) -> None:
        protected = set(supported_count_ranks(self.schema))
        runtime = {item.value for item in CountRank}
        self.assertEqual(protected, runtime)

    def test_unknown_validation_keyword_fails_closed(self) -> None:
        schema = dict(self.schema)
        schema["unknownValidationKeyword"] = True
        with self.assertRaises(UnsupportedProtectedSchemaError):
            assert_valid({}, schema)

    def test_unsupported_schema_dialect_fails_closed(self) -> None:
        schema = dict(self.schema)
        schema["$schema"] = "https://json-schema.org/draft/2019-09/schema"
        with self.assertRaises(UnsupportedProtectedSchemaError):
            assert_valid({}, schema)

    def test_unsupported_additional_properties_form_fails_closed(self) -> None:
        schema = dict(self.schema)
        schema["additionalProperties"] = {"type": "string"}
        with self.assertRaises(UnsupportedProtectedSchemaError):
            assert_valid({}, schema)


if __name__ == "__main__":
    unittest.main()
