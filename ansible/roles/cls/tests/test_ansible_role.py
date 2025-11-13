#!/usr/bin/env python3
"""
Ansible role validation tests
Tests that the role can be applied correctly
"""
import yaml
import os
import sys


def test_defaults_syntax():
    """Test that defaults/main.yml has valid YAML syntax"""
    defaults_path = os.path.join(os.path.dirname(__file__), '..', 'defaults', 'main.yml')
    with open(defaults_path, 'r') as f:
        yaml.safe_load(f)


def test_tasks_syntax():
    """Test that tasks/main.yml has valid YAML syntax"""
    tasks_path = os.path.join(os.path.dirname(__file__), '..', 'tasks', 'main.yml')
    with open(tasks_path, 'r') as f:
        yaml.safe_load(f)


def test_templates_exist():
    """Test that required templates exist"""
    templates_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
    
    required_templates = [
        'start.py.j2',
        'stop.py.j2',
        'restart.py.j2',
        'jvm.args.j2'
    ]
    
    for template in required_templates:
        template_path = os.path.join(templates_dir, template)
        assert os.path.exists(template_path), f"Template {template} does not exist"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__])

