import ast
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2] / "app"


def python_files(package: str) -> list[Path]:
    package_path = APP_ROOT / package

    return sorted(package_path.rglob("*.py"))


def module_name_from_path(path: Path) -> str:
    relative = path.relative_to(APP_ROOT)
    parts = list(relative.parts)

    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1].removesuffix(".py")

    return ".".join(["app", *parts])


def resolve_import(
    current_module: str,
    level: int,
    imported_module: str | None,
) -> str:
    current_parts = current_module.split(".")

    if level > len(current_parts):
        return ""

    base_parts = current_parts[:-level]

    if imported_module:
        base_parts.extend(imported_module.split("."))

    return ".".join(base_parts)


def collect_imports(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    current_module = module_name_from_path(path)

    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)

        elif isinstance(node, ast.ImportFrom):
            resolved = resolve_import(
                current_module=current_module,
                level=node.level,
                imported_module=node.module,
            )

            if resolved:
                imports.append(resolved)

    return imports


def assert_no_forbidden_imports(
    package: str,
    forbidden_prefixes: tuple[str, ...],
) -> None:
    violations: list[str] = []

    for path in python_files(package):
        imports = collect_imports(path)

        for imported_module in imports:
            if imported_module.startswith(forbidden_prefixes):
                violations.append(f"{module_name_from_path(path)} -> {imported_module}")

    assert not violations, (
        "Architectural dependency violations detected:\n"
        + "\n".join(sorted(violations))
    )


def test_domain_does_not_depend_on_outer_layers() -> None:
    assert_no_forbidden_imports(
        package="domain",
        forbidden_prefixes=(
            "app.api",
            "app.application",
            "app.infrastructure",
            "app.bootstrap",
            "app.database",
        ),
    )


def test_application_does_not_depend_on_outer_layers() -> None:
    assert_no_forbidden_imports(
        package="application",
        forbidden_prefixes=(
            "app.api",
            "app.infrastructure",
            "app.bootstrap",
            "app.database",
        ),
    )


def test_api_does_not_depend_directly_on_infrastructure() -> None:
    assert_no_forbidden_imports(
        package="api",
        forbidden_prefixes=(
            "app.infrastructure",
            "app.database",
        ),
    )


def test_infrastructure_does_not_depend_on_api() -> None:
    assert_no_forbidden_imports(
        package="infrastructure",
        forbidden_prefixes=("app.api",),
    )


def test_domain_only_uses_allowed_internal_modules() -> None:
    allowed_prefixes = ("app.domain",)

    violations: list[str] = []

    for path in python_files("domain"):
        for imported_module in collect_imports(path):
            if imported_module.startswith("app.") and not imported_module.startswith(
                allowed_prefixes
            ):
                violations.append(f"{module_name_from_path(path)} -> {imported_module}")

    assert not violations, (
        "Domain imports modules outside the domain layer:\n"
        + "\n".join(sorted(violations))
    )


def test_application_only_depends_on_domain_inside_app() -> None:
    allowed_prefixes = (
        "app.application",
        "app.domain",
    )

    violations: list[str] = []

    for path in python_files("application"):
        for imported_module in collect_imports(path):
            if imported_module.startswith("app.") and not imported_module.startswith(
                allowed_prefixes
            ):
                violations.append(f"{module_name_from_path(path)} -> {imported_module}")

    assert not violations, (
        "Application imports modules outside allowed layers:\n"
        + "\n".join(sorted(violations))
    )
