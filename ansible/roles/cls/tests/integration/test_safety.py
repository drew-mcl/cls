#!/usr/bin/env python3
"""
Safety and security tests for CLS role
Ensures production-ready safety
"""
import os
import re
import subprocess


def test_no_hardcoded_secrets():
    """Test that no hardcoded secrets exist in templates"""
    templates_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'templates')
    
    secret_patterns = [
        r'password\s*=\s*["\'][^"\']+["\']',
        r'secret\s*=\s*["\'][^"\']+["\']',
        r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
        r'token\s*=\s*["\'][^"\']+["\']',
    ]
    
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.j2'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    content = f.read()
                    for pattern in secret_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        assert not matches, f"Potential secret found in {file_path}: {matches}"


def test_no_dangerous_shell_commands():
    """Test that no dangerous shell commands are used"""
    templates_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'templates')
    
    dangerous_patterns = [
        r'eval\s*\(',
        r'exec\s*\(',
        r'__import__',
        r'subprocess\.call.*shell\s*=\s*True',
        r'os\.system\s*\(',
    ]
    
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.j2'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    content = f.read()
                    for pattern in dangerous_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        assert not matches, f"Dangerous pattern found in {file_path}: {matches}"


def test_file_permissions_safe():
    """Test that file permissions are safe"""
    # This is tested in molecule tests
    pass


def test_path_traversal_protection():
    """Test that scripts protect against path traversal"""
    templates_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'templates')
    
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.py.j2'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    content = f.read()
                    # Check that os.path.join is used instead of string concatenation
                    # This is a basic check - more thorough testing needed
                    if '../' in content or '..\\' in content:
                        # Make sure it's in a safe context
                        assert 'os.path.join' in content or 'os.path.abspath' in content, \
                            f"Potential path traversal in {file_path}"


def test_input_validation():
    """Test that scripts validate input"""
    # Check that scripts validate required files exist
    templates_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'templates')
    
    start_script = os.path.join(templates_dir, 'start.py.j2')
    if os.path.exists(start_script):
        with open(start_script, 'r') as f:
            content = f.read()
            # Check for validation of required files
            assert 'os.path.exists' in content or 'os.path.isfile' in content, \
                "Start script should validate file existence"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])

