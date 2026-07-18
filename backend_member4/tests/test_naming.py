import ast
import unittest
from pathlib import Path


class TestTestNaming(unittest.TestCase):
    """测试标识符编码约束。"""

    def test_all_test_method_names_are_ascii(self):
        """所有测试方法名都必须使用英文 ASCII 字符。"""
        tests_directory = Path(__file__).resolve().parent
        invalid_names = []
        for test_file in tests_directory.glob("test_*.py"):
            tree = ast.parse(test_file.read_text(encoding="utf-8"), filename=str(test_file))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                    if not node.name.isascii():
                        invalid_names.append(f"{test_file.name}:{node.lineno}:{node.name}")
        self.assertEqual(invalid_names, [], f"发现非英文测试方法名：{invalid_names}")


if __name__ == "__main__":
    unittest.main()
