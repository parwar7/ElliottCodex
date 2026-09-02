import ast
from pathlib import Path
import unittest

import support


class DependencyBoundaryTests(unittest.TestCase):
    def test_kernel_does_not_import_mutable_runtime(self) -> None:
        kernel_root = support.SRC / "elliott_methodology_kernel"
        violations = []
        for path in kernel_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                else:
                    continue
                if any(name == "elliott_runtime" or name.startswith("elliott_runtime.") for name in names):
                    violations.append(str(path))
        self.assertEqual([], violations)

    def test_runtime_imports_only_approved_public_kernel_modules(self) -> None:
        runtime_root = support.SRC / "elliott_runtime"
        approved = {
            "elliott_methodology_kernel",
            "elliott_methodology_kernel.contracts",
        }
        violations = []
        for path in runtime_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                else:
                    continue
                for name in names:
                    if name.startswith("elliott_methodology_kernel") and name not in approved:
                        violations.append(f"{path}: {name}")
        self.assertEqual([], violations)


if __name__ == "__main__":
    unittest.main()
