"""
V3 PURE - GUARD TESTS

Validates isolation rules from GUARD_V3.md to prevent V2 code contamination.

CRITICAL TESTS:
1. NO imports from backend/planning_engine/ (old V2 code)
2. Uses minuteOffset (NOT heure_debut/heure_fin strings in core)
3. Uses TypedDict types (TaskV3, Obstacle, Timeline)
4. Architecture 2-step respected (ORDERING → TIME CALCULATION)
5. rebuildTimeline() called after modifications
"""

import pytest
import ast
import sys
from pathlib import Path


# ==================== TEST: NO V2 IMPORTS ====================

def test_no_v2_imports_in_v3_modules():
    """
    GUARD: V3 modules must NOT import from backend/planning_engine/

    This prevents V2 logic contamination.
    """
    v3_module_dir = Path(__file__).parent.parent / 'backend' / 'planning_engine_v3_pure'

    assert v3_module_dir.exists(), f"V3 module directory not found: {v3_module_dir}"

    forbidden_imports = [
        'backend.planning_engine.',
        'from backend.planning_engine import',
    ]

    v3_files = list(v3_module_dir.glob('*.py'))
    assert len(v3_files) > 0, "No V3 Python files found"

    violations = []

    for py_file in v3_files:
        if py_file.name == '__init__.py':
            continue

        content = py_file.read_text(encoding='utf-8')

        for forbidden in forbidden_imports:
            if forbidden in content:
                violations.append({
                    'file': py_file.name,
                    'forbidden': forbidden,
                    'line': _find_line_number(content, forbidden)
                })

    assert len(violations) == 0, (
        f"GUARD VIOLATION: V3 modules importing from V2 code:\n" +
        "\n".join([f"  {v['file']}:{v['line']} - {v['forbidden']}" for v in violations])
    )


def _find_line_number(content: str, search_str: str) -> int:
    """Helper to find line number of string in content"""
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if search_str in line:
            return i
    return 0


# ==================== TEST: TYPES V3 USAGE ====================

def test_v3_modules_use_types_v3():
    """
    GUARD: V3 modules must import from types_v3 (TaskV3, Obstacle, Timeline)
    """
    v3_module_dir = Path(__file__).parent.parent / 'backend' / 'planning_engine_v3_pure'

    # Files that should use types_v3
    modules_requiring_types = [
        'planning_generator_v3.py',
        'timeline_calculator_v3.py',
        'data_loader_v3.py',
    ]

    for module_name in modules_requiring_types:
        module_path = v3_module_dir / module_name
        if not module_path.exists():
            continue  # Skip if not yet created

        content = module_path.read_text(encoding='utf-8')

        # Check import from types_v3
        has_types_import = (
            'from .types_v3 import' in content or
            'from backend.planning_engine_v3_pure.types_v3 import' in content
        )

        assert has_types_import, (
            f"GUARD VIOLATION: {module_name} does not import from types_v3\n"
            f"Required: from .types_v3 import TaskV3, Obstacle, Timeline"
        )


# ==================== TEST: NO STRING TIMES IN CORE ====================

def test_no_string_times_in_core_logic():
    """
    GUARD: Core V3 logic must use minuteOffset (int), NOT time strings

    Forbidden in timeline_linear.py and planning_generator_v3.py:
    - heure_debut: str
    - heure_fin: str
    - Time parsing in core logic (allowed only in display conversion)
    """
    v3_module_dir = Path(__file__).parent.parent / 'backend' / 'planning_engine_v3_pure'

    core_modules = [
        'timeline_calculator_v3.py',
        'planning_generator_v3.py',
    ]

    # Forbidden patterns (heuristic check)
    forbidden_patterns = [
        "heure_debut': '",
        "heure_fin': '",
        "'heure_debut':",
        "'heure_fin':",
    ]

    violations = []

    for module_name in core_modules:
        module_path = v3_module_dir / module_name
        if not module_path.exists():
            continue

        content = module_path.read_text(encoding='utf-8')
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith('#'):
                continue

            # Skip docstrings (heuristic: lines with only quotes)
            if '"""' in line or "'''" in line:
                continue

            for pattern in forbidden_patterns:
                if pattern in line:
                    violations.append({
                        'file': module_name,
                        'line': i,
                        'pattern': pattern,
                        'content': line.strip()
                    })

    # Allow in data_writer_v3.py (display conversion)
    violations = [v for v in violations if 'data_writer' not in v['file']]

    assert len(violations) == 0, (
        f"GUARD VIOLATION: String times in core logic (use minuteOffset instead):\n" +
        "\n".join([
            f"  {v['file']}:{v['line']} - {v['pattern']}\n    {v['content']}"
            for v in violations
        ])
    )


# ==================== TEST: REBUILD TIMELINE USAGE ====================

def test_rebuild_timeline_exists():
    """
    GUARD: rebuildTimeline() function must exist in timeline_calculator_v3.py

    This is the CORE function for V3 architecture.
    """
    timeline_module = Path(__file__).parent.parent / 'backend' / 'planning_engine_v3_pure' / 'timeline_calculator_v3.py'

    if not timeline_module.exists():
        pytest.skip("timeline_calculator_v3.py not yet created")

    content = timeline_module.read_text(encoding='utf-8')

    assert 'def rebuildTimeline(' in content, (
        "GUARD VIOLATION: rebuildTimeline() function not found in timeline_calculator_v3.py\n"
        "This is REQUIRED for V3 architecture (TIME CALCULATION step)"
    )


# ==================== TEST: FILE NAMING CONVENTION ====================

def test_v3_file_naming_convention():
    """
    GUARD: V3 files must contain '_v3' in name or be in *_v3_pure/ directory
    """
    v3_backend_dir = Path(__file__).parent.parent / 'backend' / 'planning_engine_v3_pure'

    if not v3_backend_dir.exists():
        pytest.skip("V3 backend directory not yet created")

    python_files = list(v3_backend_dir.glob('*.py'))

    # Exceptions (allowed names)
    exceptions = ['__init__.py', 'types_v3.py']

    violations = []

    for py_file in python_files:
        if py_file.name in exceptions:
            continue

        # Check if name contains '_v3' or ends with '_v3.py'
        if '_v3' not in py_file.name:
            violations.append(py_file.name)

    assert len(violations) == 0, (
        f"GUARD VIOLATION: V3 files missing '_v3' in filename:\n" +
        "\n".join([f"  {name}" for name in violations]) +
        "\nRename to include '_v3' (e.g., data_loader_v3.py)"
    )


# ==================== TEST: NO TACHES_RESPIRATOIRES REFERENCES ====================

def test_no_respiratoires_csv_references():
    """
    GUARD: V3 code must NOT reference TACHES_RESPIRATOIRES.v2.csv

    In V3, pauses are in TACHES_RECURRENTES.v3.csv with IS_PAUSE=1
    """
    v3_module_dir = Path(__file__).parent.parent / 'backend' / 'planning_engine_v3_pure'

    if not v3_module_dir.exists():
        pytest.skip("V3 backend directory not yet created")

    forbidden_pattern = 'TACHES_RESPIRATOIRES'

    violations = []

    for py_file in v3_module_dir.glob('*.py'):
        content = py_file.read_text(encoding='utf-8')

        if forbidden_pattern in content:
            # Find line number
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if forbidden_pattern in line and not line.strip().startswith('#'):
                    violations.append({
                        'file': py_file.name,
                        'line': i,
                        'content': line.strip()
                    })

    assert len(violations) == 0, (
        f"GUARD VIOLATION: References to TACHES_RESPIRATOIRES.v2.csv (REMOVED in V3):\n" +
        "\n".join([f"  {v['file']}:{v['line']} - {v['content']}" for v in violations]) +
        "\nUse TACHES_RECURRENTES.v3.csv with IS_PAUSE=1 instead"
    )


# ==================== TEST: ATOMIC WRITE PATTERN ====================

def test_atomic_write_pattern_in_data_writer():
    """
    GUARD: data_writer_v3.py must use atomic write pattern (temp + rename)
    """
    data_writer = Path(__file__).parent.parent / 'backend' / 'planning_engine_v3_pure' / 'data_writer_v3.py'

    if not data_writer.exists():
        pytest.skip("data_writer_v3.py not yet created")

    content = data_writer.read_text(encoding='utf-8')

    # Check for atomic write pattern
    has_temp_file = '.with_suffix' in content and '.tmp' in content
    has_rename = '.replace(' in content

    assert has_temp_file and has_rename, (
        "GUARD VIOLATION: data_writer_v3.py missing atomic write pattern\n"
        "Required: temp_file = path.with_suffix('.tmp') ... temp_file.replace(path)"
    )


# ==================== RUN ALL GUARDS ====================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
