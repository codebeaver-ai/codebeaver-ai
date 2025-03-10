import ast
import re
from typing import Literal

import black
import tree_sitter_typescript as tstypescript
from tree_sitter import Language, Node, Parser, Tree
from pygments.lexers import guess_lexer

import logging

logger = logging.getLogger('codebeaver')


class ContentCleaner:

    # Default supported languages, can be overridden by users
    SUPPORTED_LANGUAGES = {
        "python": {
            "aliases": ["python", "python3", "py"],
            "merge_function": "merge_python_files",
        },
        "typescript": {
            "aliases": ["typescript", "ts", "tsx", "javascript", "js", "jsx"],
            "merge_function": "merge_typescript_files",
        },
    }

    @classmethod
    def get_supported_languages(cls) -> dict:
        """Get the current supported languages configuration"""
        return cls.SUPPORTED_LANGUAGES

    @classmethod
    def set_supported_languages(cls, languages: dict) -> None:
        """Update the supported languages configuration"""
        cls.SUPPORTED_LANGUAGES = languages

    @staticmethod
    def merge_files(
        file1_path: str, file1_content: str, file2_content: str | None
    ) -> str | None:
        """
        Merge two files into one. First it detects the language of the files with guesslang,
        then uses the appropriate merge function.
        """

        def get_language() -> str | None:
            if file1_path.endswith(".py"):
                return "python"
            elif file1_path.endswith(".ts") or file1_path.endswith(".tsx"):
                return "typescript"
            elif file1_path.endswith(".js") or file1_path.endswith(".jsx"):
                return "javascript"
            return None

        file1_language = get_language()
        if file1_language is None:
            raise ValueError(
                f"Unsupported language for file1: {guess_lexer(file1_content).name}"
            )

        # Dynamically get the merge function based on the language
        merge_function_name = ContentCleaner.SUPPORTED_LANGUAGES[file1_language][
            "merge_function"
        ]
        merge_function = getattr(ContentCleaner, merge_function_name)
        return merge_function(file1_content, file2_content)

    @staticmethod
    def clean_python(content: str) -> str:
        """
        Clean and organize Python imports in a standardized format.

        Organizes imports in the following order:
        1. Module docstrings (preserved at top)
        2. Direct imports (import x)
        3. From imports (from x import y)
        4. Multiline imports
        5. Function/class definitions
        6. Main block

        Args:
            content (str): Raw Python source code

        Returns:
            str: Formatted Python code with organized imports
        """
        # Regular expressions to match Python import statements
        import_patterns = [
            r"^import\s+.*$",
            r"^from\s+.*\s+import\s+.*$",
        ]

        lines = content.splitlines()
        import_buffer = []
        import_lines = []
        in_multiline_import = False
        import_map = {}
        current_base_import = None
        function_definitions = []
        main_block = []
        current_block = []

        # Normalize line endings and remove any BOM
        lines = [line.strip("\ufeff").rstrip("\r\n") for line in lines]

        # Handle module docstring first
        docstring = []
        line_iterator = iter(lines)
        for line in line_iterator:
            stripped_line = line.strip()
            if stripped_line.startswith('"""') or stripped_line.startswith("'''"):
                docstring.append(line)
                # Handle multi-line docstrings
                if not (stripped_line.endswith('"""') or stripped_line.endswith("'''")):
                    for doc_line in line_iterator:
                        docstring.append(doc_line)
                        if doc_line.strip().endswith(
                            '"""'
                        ) or doc_line.strip().endswith("'''"):
                            break
                break
            elif stripped_line:
                break

        remaining_lines = lines[len(docstring) :]

        # Main processing loop for imports and code blocks
        for line in remaining_lines:
            stripped_line = line.strip()
            if any(
                re.match(pattern, stripped_line) for pattern in import_patterns
            ):  # Extract base import without comments and parentheses
                base_import = stripped_line.split("#")[0]
                base_import = base_import.split("(")[0].strip()
                base_import = " ".join(base_import.split())

                # Handle multiline imports
                if "(" in stripped_line and ")" not in stripped_line:
                    in_multiline_import = True
                    import_buffer = [line]
                    current_base_import = base_import
                else:
                    if line not in import_lines:
                        import_lines.append(line)
            elif in_multiline_import:
                import_buffer.append(line)
                if ")" in stripped_line:
                    # Process complete multiline import
                    in_multiline_import = False
                    complete_import = "\n".join(import_buffer)

                    # Merge with existing imports if needed
                    if current_base_import in import_map:
                        existing_items = import_map[current_base_import]
                        new_items = complete_import[
                            complete_import.find("(") + 1 : complete_import.rfind(")")
                        ].strip()

                        all_items = []
                        for item_list in [
                            existing_items.split(","),
                            new_items.split(","),
                        ]:
                            for item in item_list:
                                clean_item = item.strip().strip("\n").strip(",")
                                if clean_item and clean_item not in all_items:
                                    all_items.append(clean_item)

                        indent_match = re.match(r"^\s*", import_buffer[1])
                        indent = indent_match.group(0) if indent_match else ""
                        combined_items = ",\n".join(
                            f"{indent}{item}" for item in sorted(all_items)
                        )
                        import_map[current_base_import] = combined_items
                    else:
                        items = complete_import[
                            complete_import.find("(") + 1 : complete_import.rfind(")")
                        ].strip()

                        indent_match = re.match(r"^\s*", import_buffer[1])
                        indent = indent_match.group(0) if indent_match else ""
                        import_map[current_base_import] = "\n".join(
                            f"{indent}{item.strip()}" for item in items.split("\n")
                        )

                    import_buffer = []
            else:
                # Handle non-import code blocks
                if stripped_line:
                    if stripped_line.startswith("def ") or stripped_line.startswith(
                        "class "
                    ):  # Start new function/class block
                        if current_block:
                            function_definitions.append("\n".join(current_block))
                            current_block = []
                        current_block = [line]
                    elif stripped_line.startswith(
                        'if __name__ == "__main__"'
                    ):  # Handle main block
                        if current_block:
                            function_definitions.append("\n".join(current_block))
                        current_block = None
                        main_block = [line]
                    elif main_block and current_block is None:
                        main_block.append(line)
                    elif current_block is not None:
                        current_block.append(line)
                    else:
                        function_definitions.append(line)

        if current_block:
            function_definitions.append("\n".join(current_block))

        # Assemble final content in correct order
        final_content = []
        if docstring:
            final_content.extend(docstring)

        # Sort single-line imports
        single_line_imports = []
        for line in import_lines:
            if "(" not in line:
                single_line_imports.append(line)
        single_line_imports.sort(reverse=True)

        # Sort multiline imports
        multiline_imports = []
        for base_import, items in sorted(import_map.items()):
            # Get base indentation from first item
            base_indent_match = re.match(r"^\s*", base_import)
            base_indent = base_indent_match.group(0) if base_indent_match else ""
            aggregated_import = f"{base_import} (\n{items}\n{base_indent[:-4]})"
            multiline_imports.append(aggregated_import)

        # Group and sort by type
        direct_imports = set()
        single_line_from_imports = set()
        multiline_from_imports = set()

        for line in single_line_imports:
            if line.startswith("import "):
                direct_imports.add(line)
            else:
                single_line_from_imports.add(line)

        for import_stmt in multiline_imports:
            if import_stmt.startswith("import "):
                direct_imports.add(import_stmt)
            else:
                multiline_from_imports.add(import_stmt)

        # Combine in correct order
        all_imports = (
            sorted(direct_imports)
            + sorted(single_line_from_imports)
            + sorted(multiline_from_imports)
        )

        if all_imports:
            final_content.extend(all_imports)
            final_content.append("")
        if function_definitions:
            final_content.extend(
                [
                    "\n".join(function_definitions)
                    .replace("\ndef ", "\n\ndef ")
                    .replace("\nclass ", "\n\nclass ")
                ]
            )
        if main_block:
            if function_definitions:
                final_content.append("")  # Add blank line before main block
            final_content.extend(main_block)

        return "\n".join(final_content)

    @staticmethod
    def clean_typescript(content: str) -> str:
        lines = content.splitlines()
        import_buffer = []
        import_blocks = {}  # Dict to store sets of imports per module
        type_import_blocks = {}  # Dict to store sets of type imports per module
        other_lines = []
        in_multiline_import = False

        def parse_imports(import_text: str) -> set[str]:
            start = import_text.find("{")
            end = import_text.rfind("}")
            if start == -1 or end == -1:
                return set()
            items = import_text[start + 1 : end]
            return {item.strip() for item in items.split(",") if item.strip()}

        lines = [line.strip("\ufeff").rstrip("\r\n") for line in lines]

        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith("import "):
                is_type_import = "type {" in line
                target_blocks = type_import_blocks if is_type_import else import_blocks

                if "{" in line and "}" not in line:
                    in_multiline_import = True
                    import_buffer = [line]
                else:
                    module_path = line.split("from ")[-1].strip("'; ")
                    current_imports = parse_imports(line)
                    if module_path in target_blocks:
                        target_blocks[module_path].update(current_imports)
                    else:
                        target_blocks[module_path] = current_imports
            elif in_multiline_import:
                import_buffer.append(line)
                if "}" in line:
                    in_multiline_import = False
                    full_import = "\n".join(import_buffer)
                    is_type_import = "type {" in full_import
                    target_blocks = (
                        type_import_blocks if is_type_import else import_blocks
                    )
                    module_path = full_import.split("from ")[-1].strip("'; ")
                    current_imports = parse_imports(full_import)
                    if module_path in target_blocks:
                        target_blocks[module_path].update(current_imports)
                    else:
                        target_blocks[module_path] = current_imports
                    import_buffer = []
            elif stripped_line:
                other_lines.append(line)

        final_content = []

        # Regular imports first
        for module_path in sorted(import_blocks.keys()):
            items = sorted(import_blocks[module_path])
            if len(items) == 1:
                final_content.append(f"import {{ {items[0]} }} from '{module_path}';")
            elif items:
                final_content.extend(
                    [
                        "import {",
                        *[f"    {item}," for item in items[:-1]],
                        f"    {items[-1]}",
                        f"}} from '{module_path}';",
                    ]
                )

        # Type imports second
        for module_path in sorted(type_import_blocks.keys()):
            items = sorted(type_import_blocks[module_path])
            if len(items) == 1:
                final_content.append(
                    f"import type {{ {items[0]} }} from '{module_path}';"
                )
            elif items:
                final_content.extend(
                    [
                        "import type {",
                        *[f"    {item}," for item in items[:-1]],
                        f"    {items[-1]}",
                        f"}} from '{module_path}';",
                    ]
                )

        final_content.append("")
        final_content.extend(other_lines)
        return "\n".join(final_content).strip()

    @staticmethod
    def merge_python_files(file1_content: str, file2_content: str) -> str | None:

        file2_content = (
            file2_content.replace("// ... existing code", "")
            .replace("// ... existing tests", "")
            .replace("... existing code", "")
            .replace("... existing tests", "")
        )
        try:
            tree1 = ast.parse(file1_content)
            tree2 = ast.parse(file2_content)
        except Exception:
            return None

        # Collect imports
        module_variables = {}
        imports = {}
        imports_by_module = {}
        conditional_imports = {}
        other_code = {}
        try_except_blocks = {}

        def extract_class_variables(node: ast.ClassDef) -> dict:
            variables = {}
            for item in node.body:
                if isinstance(item, ast.AnnAssign):
                    # Handle annotated assignments like: x: int = 1
                    var_name = item.target.id  # type: ignore
                    variables[var_name] = {
                        "node": item,
                        "annotation": ast.unparse(item.annotation),
                        "value": ast.unparse(item.value) if item.value else None,
                    }
                elif isinstance(item, ast.Assign) and item.targets:
                    # Handle regular assignments like: x = 1
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            variables[target.id] = {
                                "node": item,
                                "annotation": None,
                                "value": ast.unparse(item.value),
                            }
            return variables

        def get_type_annotation(
            node: ast.FunctionDef | ast.AsyncFunctionDef,
        ) -> str | None:
            if hasattr(node, "returns"):
                return ast.unparse(node.returns) if node.returns else None
            return None

        def get_arg_annotations(args: ast.arguments) -> dict[str, str]:
            annotations = {}
            for arg in args.args:
                if arg.annotation:
                    annotations[arg.arg] = ast.unparse(arg.annotation)
            return annotations

        def merge_decorators(
            existing_node: ast.AST, new_node: ast.AST
        ) -> list[ast.expr]:
            existing_decorators = getattr(existing_node, "decorator_list", [])
            new_decorators = getattr(new_node, "decorator_list", [])

            # Create a set of decorator strings for comparison
            existing_dec_strs = {ast.unparse(dec) for dec in existing_decorators}
            merged_decorators = existing_decorators.copy()

            # Add new decorators that don't exist yet
            for dec in new_decorators:
                if ast.unparse(dec) not in existing_dec_strs:
                    merged_decorators.append(dec)

            return merged_decorators

        def process_module_variables(node: ast.AST) -> None:
            if isinstance(node, ast.Assign):
                # Handle simple assignments
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        module_variables[target.id] = ast.unparse(node)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                module_variables[node.target.id] = ast.unparse(node)

        def process_node_for_imports(
            node: ast.AST, parent_if: ast.If | None = None
        ) -> None:
            if isinstance(node, ast.Try):
                # Skip processing imports in try blocks since they're handled separately
                return
            if isinstance(node, ast.If):
                # Create full if/elif/else block structure
                current_node = node
                conditions = []

                while current_node:
                    # Handle if/elif body
                    condition = ast.unparse(current_node.test)
                    imports_in_block = []
                    for child in current_node.body:
                        if isinstance(child, ast.Import | ast.ImportFrom):
                            imports_in_block.append(ast.unparse(child))

                    if imports_in_block:
                        conditions.append((condition, imports_in_block))

                    # Handle else body
                    if current_node.orelse:
                        if len(current_node.orelse) == 1 and isinstance(
                            current_node.orelse[0], ast.If
                        ):
                            # This is an elif
                            current_node = current_node.orelse[0]
                        else:
                            # This is an else
                            else_imports = []
                            for child in current_node.orelse:
                                if isinstance(child, ast.Import | ast.ImportFrom):
                                    else_imports.append(ast.unparse(child))
                            if else_imports:
                                conditions.append(("else", else_imports))
                            break
                    else:
                        break

                # Store the complete if/elif/else chain
                if conditions:
                    block_key = f"if_{len(conditional_imports)}"
                    conditional_imports[block_key] = conditions

            elif isinstance(node, (ast.Import | ast.ImportFrom)):
                if parent_if:
                    return  # Skip as these are handled in the If block processing
                # Handle regular imports as before
                if isinstance(node, ast.ImportFrom):
                    module = node.module
                    if module not in imports_by_module:
                        imports_by_module[module] = set()
                    for _module in imports_by_module:
                        for name in node.names:
                            if name.name in imports_by_module[_module]:
                                imports_by_module[_module].remove(name.name)
                    for name in node.names:
                        imports_by_module[module].add(name.name)
                else:
                    imports[ast.unparse(node)] = ast.unparse(node)

            # Process nested nodes
            for child in ast.iter_child_nodes(node):
                process_node_for_imports(
                    child, parent_if or (node if isinstance(node, ast.If) else None)
                )

        # Process both files for imports
        for tree in [tree1, tree2]:
            for node in tree.body:
                process_module_variables(node)
                process_node_for_imports(node)
                if isinstance(node, ast.Try):
                    block_key = ast.unparse(node)
                    try_except_blocks[block_key] = node

        formatted_imports = []
        for module, names in sorted(imports_by_module.items()):
            if len(names) > 0:
                names_str = ",\n    ".join(sorted(names))
                import_str = f"from {module} import (\n    {names_str},\n)"
                formatted_imports.append(import_str)

        # Build class and function map from both files
        definitions = {}
        for node in tree1.body:
            if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
                docstring = ast.get_docstring(node)
                if isinstance(node, ast.ClassDef):
                    methods = {}
                    class_vars = extract_class_variables(node)
                    for method in node.body:
                        if isinstance(method, ast.FunctionDef | ast.AsyncFunctionDef):
                            method_docstring = ast.get_docstring(method)
                            methods[method.name] = {
                                "node": method,
                                "docstring": method_docstring,
                                "return_type": get_type_annotation(method),
                                "arg_types": get_arg_annotations(method.args),
                            }
                    definitions[node.name] = {
                        "node": node,
                        "methods": methods,
                        "docstring": docstring,
                        "variables": class_vars,
                    }
                else:
                    definitions[node.name] = {
                        "node": node,
                        "docstring": docstring,
                        "return_type": get_type_annotation(node),
                        "arg_types": get_arg_annotations(node.args),
                    }
            elif isinstance(node, ast.If):
                other_code[ast.unparse(node)] = ast.unparse(node)

        # Merge or override with file2 definitions
        for node in tree2.body:
            if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
                docstring = ast.get_docstring(node)
                if isinstance(node, ast.ClassDef):
                    class_vars = extract_class_variables(node)
                    if node.name in definitions:
                        existing_class = definitions[node.name]
                        existing_class["variables"].update(class_vars)
                        if docstring:
                            existing_class["docstring"] = docstring
                        existing_class["node"].decorator_list = merge_decorators(
                            existing_class["node"], node
                        )
                        for method in node.body:
                            if isinstance(
                                method, ast.FunctionDef | ast.AsyncFunctionDef
                            ):
                                method_docstring = ast.get_docstring(method)
                                if method.name in existing_class["methods"]:
                                    # Merge method decorators
                                    method.decorator_list = merge_decorators(
                                        existing_class["methods"][method.name]["node"],
                                        method,
                                    )
                                existing_class["methods"][method.name] = {
                                    "node": method,
                                    "docstring": method_docstring,
                                    "return_type": get_type_annotation(method),
                                    "arg_types": get_arg_annotations(method.args),
                                }
                        # Update class body with merged methods
                        definitions[node.name] = existing_class
                    else:
                        methods = {}
                        for method in node.body:
                            if isinstance(
                                method, ast.FunctionDef | ast.AsyncFunctionDef
                            ):
                                method_docstring = ast.get_docstring(method)
                                methods[method.name] = {
                                    "node": method,
                                    "docstring": method_docstring,
                                    "return_type": get_type_annotation(method),
                                    "arg_types": get_arg_annotations(method.args),
                                }
                        definitions[node.name] = {
                            "node": node,
                            "methods": methods,
                            "docstring": docstring,
                            "variables": class_vars,
                        }
                else:
                    if node.name in definitions:
                        # Merge function decorators
                        node.decorator_list = merge_decorators(
                            definitions[node.name]["node"], node
                        )
                    definitions[node.name] = {"node": node, "docstring": docstring}

        # Reconstruct class instances
        for _, def_info in definitions.items():
            if isinstance(def_info["node"], ast.ClassDef):
                def_info["node"].body = [
                    m for m in def_info["node"].body if isinstance(m, ast.ClassDef)
                ]
                if def_info["docstring"]:
                    def_info["node"].body.extend(
                        [
                            ast.Expr(ast.Constant(def_info["docstring"], kind="str"))  # type: ignore
                        ]
                    )
                # Add class variables
                for var_name, var_info in def_info["variables"].items():
                    if var_info["annotation"]:
                        # Recreate annotated assignment
                        def_info["node"].body.append(
                            ast.AnnAssign(
                                target=ast.Name(id=var_name, ctx=ast.Store()),
                                annotation=ast.parse(var_info["annotation"])
                                .body[0]
                                .value,  # type: ignore
                                value=(
                                    ast.parse(var_info["value"]).body[0].value  # type: ignore
                                    if var_info["value"]
                                    else None
                                ),
                                simple=1,
                                lineno=1,
                            )
                        )
                    elif var_info["value"]:
                        # Recreate regular assignment
                        def_info["node"].body.append(
                            ast.Assign(
                                targets=[ast.Name(id=var_name, ctx=ast.Store())],
                                value=ast.parse(var_info["value"]).body[0].value,  # type: ignore
                                lineno=1,
                            )
                        )
                # Reconstruct methods with type annotations
                for method_info in def_info["methods"].values():
                    method = method_info["node"]
                    if method_info["return_type"]:
                        method.returns = (
                            ast.parse(method_info["return_type"]).body[0].value  # type: ignore
                        )
                    for arg_name, arg_type in method_info["arg_types"].items():
                        for arg in method.args.args:
                            if arg.arg == arg_name:
                                arg.annotation = ast.parse(arg_type).body[0].value  # type: ignore
                    def_info["node"].body.append(method)

        conditional_import_blocks = []
        for _, block_conditions in conditional_imports.items():
            block_lines = []
            for i, (condition, _imports) in enumerate(block_conditions):
                prefix = "if" if i == 0 else "elif" if condition != "else" else "else"
                if condition != "else":
                    block_lines.append(f"{prefix} {condition}:")
                else:
                    block_lines.append(f"{prefix}:")
                block_lines.extend(f"    {imp}" for imp in _imports)
            conditional_import_blocks.append("\n".join(block_lines))

        result_parts = [
            *sorted(imports.values()),
            *sorted(formatted_imports),
            *conditional_import_blocks,
            *[
                "\n" + ast.unparse(block) for block in try_except_blocks.values()
            ],  # Add this line
            "",
            *sorted(module_variables.values()),
            "",
            *["\n" + ast.unparse(node["node"]) for node in definitions.values()],
            *sorted(other_code.values()),
        ]

        merged_content = "\n".join(result_parts).replace("\n\n\n", "\n\n")
        logger.debug("Merged content:\n\n" + merged_content)
        try:
            ast.parse(merged_content)
            merged_content = black.format_str(merged_content, mode=black.Mode())
            return merged_content
        except SyntaxError:
            return None

    @staticmethod
    def merge_typescript_files(
        file1_content: str, file2_content: str, language: Literal["tsx"] | Literal["ts"]
    ) -> str | None:
        if language == "ts":
            parser = Parser(Language(tstypescript.language_typescript()))
        else:
            parser = Parser(Language(tstypescript.language_tsx()))

        file2_content = (
            file2_content.replace("// ... existing code", "")
            .replace("// ... existing tests", "")
            .replace("... existing code", "")
            .replace("... existing tests", "")
        )

        try:
            tree1 = parser.parse(bytes(file1_content, "utf8"))
            tree2 = parser.parse(bytes(file2_content, "utf8"))
        except Exception:
            return None

        imports_by_module = {}
        type_imports = {}
        expressions = {}
        class_definitions = {}
        function_definitions = {}
        default_exports = {}
        test_hooks = {}
        test_scenarios = {}
        # Track unique declarations and hooks
        declarations = set()
        hooks = {}

        def merge_mock_declarations(node: Node, content: str, mocks: dict) -> None:
            """Extract and merge jest.mock declarations"""
            mock_call = content[node.start_byte : node.end_byte]
            mocks[f"mock_{len(mocks)}"] = mock_call

        def extract_test_hooks(
            node: Node, content: str, hooks: dict[str, list[str]]
        ) -> None:
            """Extract test lifecycle hooks like beforeEach, afterEach, beforeAll, afterAll"""
            hook_text = content[node.start_byte : node.end_byte]

            hook_types = ["beforeEach", "afterEach", "beforeAll", "afterAll"]
            hook_type = next((h for h in hook_types if hook_text.startswith(h)), None)

            if hook_type:
                # Extract just the function body
                body_start = hook_text.find("=>") + 2
                body = hook_text[body_start:].strip().strip("{}; ").strip("\n})")
                if hook_type not in hooks:
                    hooks[hook_type] = []
                hooks[hook_type].append(body)

        def merge_test_hooks(hooks: dict[str, list[str]]) -> dict[str, str]:
            """Combine multiple hooks of the same type into a single declaration"""
            merged = {}
            for hook_type, bodies in hooks.items():
                # Filter empty bodies and combine with proper indentation
                valid_bodies = [body.strip() for body in bodies if body.strip()]
                if valid_bodies:
                    combined_body = "\n  ".join(valid_bodies)
                    merged[f"test_hook_{hook_type}"] = (
                        f"{hook_type}(() => {{\n  {combined_body}\n}});"
                    )
            return merged

        def extract_test_scenarios(
            node: Node, content: str, scenarios: dict[str, dict]
        ) -> None:
            scenario_text = content[node.start_byte : node.end_byte]
            prev_node = node.prev_sibling

            docstring = ""
            if prev_node and prev_node.type == "comment":
                docstring = content[prev_node.start_byte : prev_node.end_byte] + "\n"

            if scenario_text.startswith(("describe(", "test(")):
                # Extract scenario name
                name_start = scenario_text.find("(") + 1
                name_end = scenario_text.find(",")
                scenario_name = scenario_text[name_start:name_end].strip("' \"")

                # Extract full scenario body including comments and tests
                body_start = scenario_text.find("=> {") + 4
                body_end = scenario_text.rfind("}")
                body = scenario_text[body_start:body_end].strip()

                # Split the body into lines for processing
                lines = body.split("\n")
                processed_lines = []

                current_block = []
                in_hook = False
                hook_type = None

                for line in lines:
                    stripped = line.strip()

                    # Check for hook start
                    if any(
                        hook in stripped
                        for hook in ["beforeAll", "beforeEach", "afterAll", "afterEach"]
                    ):
                        in_hook = True
                        hook_type = next(
                            hook
                            for hook in [
                                "beforeAll",
                                "beforeEach",
                                "afterAll",
                                "afterEach",
                            ]
                            if hook in stripped
                        )
                        current_block = [line]
                        continue

                    # Check for mock declarations
                    if (
                        "jest.fn()" in stripped
                        or "jest.spyOn(" in stripped
                        or "jest.mock(" in stripped
                    ):
                        declaration = re.sub(r"\s+", " ", stripped)
                        if declaration not in declarations:
                            declarations.add(declaration)
                            processed_lines.append(line)
                        continue

                    # Handle hook blocks
                    if in_hook:
                        current_block.append(line)
                        if stripped.endswith("});"):
                            in_hook = False
                            hook_content = "\n".join(current_block)
                            if hook_type not in hooks:
                                hooks[hook_type] = hook_content
                                processed_lines.extend(current_block)
                        continue

                    # Add non-mock, non-hook lines
                    processed_lines.append(line)

                processed_body = "\n".join(processed_lines)

                if scenario_name not in scenarios:
                    scenarios[scenario_name] = {"body": processed_body}
                else:
                    # Merge bodies of scenarios with same name
                    existing_body = scenarios[scenario_name]["body"]
                    scenarios[scenario_name][
                        "body"
                    ] = f"{existing_body}\n    {processed_body}"
                scenarios[scenario_name]["type"] = (
                    "describe" if "describe(" in scenario_text else "test"
                )
                scenarios[scenario_name]["docstring"] = docstring

        def merge_test_scenarios(scenarios: dict[str, dict]) -> dict[str, str]:
            merged = {}
            for scenario_name, data in scenarios.items():
                merged[f"test_scenario_{scenario_name}"] = (
                    f"{('describe(' if data['type'] == 'describe' else 'test(')}'{scenario_name}', () => {{\n{data['docstring'] if data['docstring'] else ''} {data['body']}\n}});"
                )
            return merged

        def extract_class_content(node: Node, content: str) -> dict[str, str]:
            class_body_node = next(
                (child for child in node.children if child.type == "class_body"), None
            )
            if not class_body_node:
                return {}

            methods = {}
            for member in class_body_node.children:
                if member.type == "method_definition":
                    method_name_node = next(
                        (
                            child
                            for child in member.children
                            if child.type == "property_identifier"
                        ),
                        None,
                    )
                    if method_name_node:
                        method_name = content[
                            method_name_node.start_byte : method_name_node.end_byte
                        ]
                        methods[method_name] = content[
                            member.start_byte : member.end_byte
                        ]
            return methods

        def process_imports(node: Node, content: str) -> None:
            import_text = content[node.start_byte : node.end_byte]
            if "type {" in import_text:
                type_imports[import_text] = import_text
                return

            if "from" in import_text:
                module = import_text.split("from")[1].strip()
            else:
                module = import_text.split("import")[1].strip()
            module = module.strip("\"'").strip(";").strip('"').strip("'")
            if module not in imports_by_module:
                imports_by_module[module] = set()

            if "{" in import_text:
                # Handle destructured imports
                items_str = import_text[
                    import_text.find("{") + 1 : import_text.find("}")
                ]
                items = [item.strip() for item in items_str.split(",") if item.strip()]
                imports_by_module[module].update(items)
            else:
                # Handle default imports
                if "import" in import_text and "from" in import_text:
                    import_name = (
                        import_text.split("import")[1].split("from")[0].strip()
                    )
                    imports_by_module[module].add(f"default:{import_name}")
                else:
                    import_name = import_text.split("import")[1].strip()
                    imports_by_module[module].add(f"module:{import_name}")

        def process_tree(tree: Tree, content: str, is_override: bool = False) -> None:
            mock_declarations = {}

            for node in tree.root_node.children:
                export_statement = None
                if node.type == "export_statement":
                    default = next(
                        (child for child in node.children if child.type == "default"),
                        None,
                    )
                    if default:
                        node_name = next(
                            (
                                child
                                for child in node.children
                                if child.type == "identifier"
                            ),
                            None,
                        )
                        if node_name:
                            default_exports[node_name.text] = content[
                                node.start_byte : node.end_byte
                            ]
                            continue
                    else:
                        export_statement = node
                        node = node.children[1]
                if node.type == "import_statement":
                    process_imports(node, content)
                elif node.type == "lexical_declaration":
                    declarator = next(
                        (
                            child
                            for child in node.children
                            if child.type == "variable_declarator"
                        ),
                        None,
                    )
                    if declarator:
                        name_node = next(
                            (
                                child
                                for child in declarator.children
                                if child.type == "identifier"
                            ),
                            None,
                        )
                        if name_node:
                            func_name = content[
                                name_node.start_byte : name_node.end_byte
                            ]
                            if export_statement:
                                _node = export_statement
                                _node.children[1] = node
                                node = _node
                            if is_override or func_name not in function_definitions:
                                function_definitions[func_name] = (
                                    "\n" + content[node.start_byte : node.end_byte]
                                )
                elif node.type in [
                    "type_alias_declaration",
                    "interface_declaration",
                    "statement_block",
                    "expression_statement",
                    "enum_declaration",
                    "ambient_declaration",
                    "module",
                ]:
                    if node.type == "expression_statement":
                        expression_text = content[node.start_byte : node.end_byte]
                        if "jest.mock(" in expression_text:
                            merge_mock_declarations(node, content, mock_declarations)
                            continue
                        if "describe(" in expression_text or "test(" in expression_text:
                            extract_test_scenarios(node, content, test_scenarios)
                        if any(
                            hook in expression_text
                            for hook in [
                                "beforeEach",
                                "afterEach",
                                "beforeAll",
                                "afterAll",
                            ]
                        ):
                            extract_test_hooks(node, content, test_hooks)
                            continue
                    name_node = next(
                        (
                            child
                            for child in node.children
                            if child.type
                            in [
                                "type_identifier",
                                "labeled_statement",
                                "lexical_declaration",
                                "internal_module",
                                "identifier",
                                "module",
                            ]
                        ),
                        None,
                    )
                    if name_node:
                        type_name = content[name_node.start_byte : name_node.end_byte]
                        if export_statement:
                            _node = export_statement
                            _node.children[1] = node
                            node = _node
                        if is_override or type_name not in expressions:
                            expressions[type_name] = (
                                "\n" + content[node.start_byte : node.end_byte]
                            )

                elif node.type == "function_declaration":
                    name_node = next(
                        (
                            child
                            for child in node.children
                            if child.type == "identifier"
                        ),
                        None,
                    )
                    if name_node:
                        func_name = content[name_node.start_byte : name_node.end_byte]
                        if export_statement:
                            _node = export_statement
                            _node.children[1] = node
                            node = _node
                        if is_override or func_name not in function_definitions:
                            function_definitions[func_name] = (
                                "\n" + content[node.start_byte : node.end_byte]
                            )

                elif node.type == "class_declaration":
                    name_node = next(
                        (
                            child
                            for child in node.children
                            if child.type == "type_identifier"
                        ),
                        None,
                    )
                    if name_node:
                        class_name = content[name_node.start_byte : name_node.end_byte]
                        methods = extract_class_content(node, content)

                        if export_statement:
                            _node = export_statement
                            _node.children[1] = node
                            node = _node
                        if class_name not in class_definitions:
                            class_definitions[class_name] = {
                                "node": node,
                                "content": content,
                                "methods": methods,
                            }
                        elif is_override:
                            # Merge methods, with file2 methods taking precedence
                            class_definitions[class_name]["methods"].update(methods)
                            class_definitions[class_name]["node"] = node
                            class_definitions[class_name]["content"] = content

            for module_path, implementation in mock_declarations.items():
                expressions[f"jest_mock_{module_path}"] = implementation
            merged_hooks = merge_test_hooks(test_hooks)
            for hook_title, hook_impl in merged_hooks.items():
                expressions[hook_title] = f"\n{hook_impl}"
            merged_scenarios = merge_test_scenarios(test_scenarios)
            for scenario_title, scenario_impl in merged_scenarios.items():
                expressions[scenario_title] = f"\n{scenario_impl}"

        # Process both files
        process_tree(tree1, file1_content)
        process_tree(tree2, file2_content, is_override=True)

        # Format imports
        formatted_imports = []
        for module, items in sorted(imports_by_module.items()):
            default_imports = [
                item.replace("default:", "")
                for item in items
                if item.startswith("default:")
            ]
            module_imports = [
                item.replace("module:", "")
                for item in items
                if item.startswith("module:")
            ]
            named_imports = [
                item
                for item in items
                if not item.startswith("default:") and not item.startswith("module:")
            ]

            if default_imports:
                formatted_imports.append(
                    f"import {default_imports[0]} from '{module}';"
                )
            if module_imports:
                formatted_imports.extend(
                    [f"import '{module}';" for item in module_imports]
                )

            if named_imports:
                if len(named_imports) == 1:
                    formatted_imports.append(
                        f"import {{ {named_imports[0]} }} from '{module}';"
                    )
                else:
                    formatted_imports.extend(
                        [
                            "import {",
                            *[f"    {item}," for item in sorted(named_imports)],
                            f"}} from '{module}';",
                        ]
                    )

        # Reconstruct merged classes
        merged_classes = []
        for _, class_def in class_definitions.items():
            class_node = class_def["node"]
            class_start = class_def["content"][
                class_node.start_byte : class_node.start_byte
                + class_node.text.find(bytes("{", "utf8"))
                + 1
            ]
            methods_text = (
                "\n    " + "\n    ".join(class_def["methods"].values()) + "\n"
            )
            class_text = class_start + methods_text + "}"
            merged_classes.append(class_text)

        result_parts = [
            *formatted_imports,
            *sorted(type_imports.values()),
            "",
            *[
                mock for mock in sorted(expressions.values()) if "jest.mock" in mock
            ],  # Mocks first
            *[
                expr for expr in sorted(expressions.values()) if "jest.mock" not in expr
            ],  # Other expressions
            "",
            *function_definitions.values(),
            "",
            *merged_classes,
            "",
            *sorted(default_exports.values()),
        ]

        merged_content = (
            "\n".join(result_parts)
            .replace("// ... existing code", "")
            .replace("// ... existing tests", "")
            .replace("\n\n\n", "\n\n")
        )
        logger.debug("Merged content:\n\n" + merged_content)
        tree = parser.parse(bytes(merged_content, "utf8"))
        has_errors = False
        for node in tree.root_node.children:
            if node.type == "ERROR":
                has_errors = True
                break

        if has_errors:
            return None
        return merged_content
