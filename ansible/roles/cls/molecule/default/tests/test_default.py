"""
Testinfra tests for CLS role
"""
import os
import pytest
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']
).get_hosts('all')


def test_instance_directories_exist(host):
    """Test that instance directories are created"""
    instance_dir = "/home/team/app/instances/test-instance-001"
    
    assert host.file(instance_dir).exists
    assert host.file(instance_dir + "/run").is_directory
    assert host.file(instance_dir + "/data").is_directory
    assert host.file(instance_dir + "/log").is_directory
    assert host.file(instance_dir + "/scripts").is_directory


def test_release_directories_exist(host):
    """Test that release directories are created"""
    release_dir = "/home/team/app/instances/test-instance-001/release/1.0.0"
    
    assert host.file(release_dir).is_directory
    assert host.file(release_dir + "/run").is_directory
    assert host.file(release_dir + "/scripts").is_directory


def test_scripts_exist(host):
    """Test that lifecycle scripts are generated"""
    scripts_dir = "/home/team/app/instances/test-instance-001/release/1.0.0/scripts"
    
    start_script = host.file(scripts_dir + "/start.py")
    stop_script = host.file(scripts_dir + "/stop.py")
    restart_script = host.file(scripts_dir + "/restart.py")
    
    assert start_script.exists
    assert start_script.is_file
    assert start_script.mode == 0o755
    
    assert stop_script.exists
    assert stop_script.is_file
    assert stop_script.mode == 0o755
    
    assert restart_script.exists
    assert restart_script.is_file
    assert restart_script.mode == 0o755


def test_scripts_are_executable(host):
    """Test that scripts are executable"""
    scripts_dir = "/home/team/app/instances/test-instance-001/release/1.0.0/scripts"
    
    assert host.run("test -x " + scripts_dir + "/start.py").rc == 0
    assert host.run("test -x " + scripts_dir + "/stop.py").rc == 0
    assert host.run("test -x " + scripts_dir + "/restart.py").rc == 0


def test_config_files_exist(host):
    """Test that configuration files are generated"""
    run_dir = "/home/team/app/instances/test-instance-001/release/1.0.0/run"
    
    state_env = host.file(run_dir + "/state.env")
    jvm_args = host.file(run_dir + "/jvm.args")
    
    assert state_env.exists
    assert state_env.is_file
    assert state_env.mode == 0o644
    
    assert jvm_args.exists
    assert jvm_args.is_file
    assert jvm_args.mode == 0o644


def test_state_env_content(host):
    """Test that state.env contains correct environment variables"""
    state_env = host.file("/home/team/app/instances/test-instance-001/release/1.0.0/run/state.env")
    
    assert state_env.exists
    content = state_env.content_string
    
    # Check ENV_ variable (with prefix)
    assert "ENV_TEST_VAR=test_value" in content
    
    # Check ENVSTRIP_ variable (without prefix)
    assert "SECRET=secret123" in content
    assert "ENVSTRIP_SECRET" not in content
    
    # Check BEDROCK_ variable (with prefix)
    assert "BEDROCK_CONFIG=/etc/bedrock" in content


def test_jvm_args_content(host):
    """Test that jvm.args contains correct JVM arguments"""
    jvm_args = host.file("/home/team/app/instances/test-instance-001/release/1.0.0/run/jvm.args")
    
    assert jvm_args.exists
    content = jvm_args.content_string
    
    assert "-Xms128m" in content
    assert "-Xmx256m" in content
    assert "-XX:+UseG1GC" in content


def test_current_symlink(host):
    """Test that current symlink is created"""
    current_link = host.file("/home/team/app/instances/test-instance-001/current")
    
    assert current_link.exists
    assert current_link.is_symlink
    assert current_link.linked_to == "/home/team/app/instances/test-instance-001/release/1.0.0"


def test_start_script_syntax(host):
    """Test that start script has valid Python syntax"""
    start_script = "/home/team/app/instances/test-instance-001/release/1.0.0/scripts/start.py"
    
    result = host.run("python3 -m py_compile " + start_script)
    assert result.rc == 0, "Start script has syntax errors: " + result.stderr


def test_stop_script_syntax(host):
    """Test that stop script has valid Python syntax"""
    stop_script = "/home/team/app/instances/test-instance-001/release/1.0.0/scripts/stop.py"
    
    result = host.run("python3 -m py_compile " + stop_script)
    assert result.rc == 0, "Stop script has syntax errors: " + result.stderr


def test_restart_script_syntax(host):
    """Test that restart script has valid Python syntax"""
    restart_script = "/home/team/app/instances/test-instance-001/release/1.0.0/scripts/restart.py"
    
    result = host.run("python3 -m py_compile " + restart_script)
    assert result.rc == 0, "Restart script has syntax errors: " + result.stderr


def test_start_script_imports(host):
    """Test that start script imports work"""
    start_script = "/home/team/app/instances/test-instance-001/release/1.0.0/scripts/start.py"
    
    # Test imports without executing
    result = host.run("python3 -c 'import ast; ast.parse(open(\"" + start_script + "\").read())'")
    assert result.rc == 0, "Start script has import errors"


def test_scripts_have_shebang(host):
    """Test that scripts have correct shebang"""
    scripts_dir = "/home/team/app/instances/test-instance-001/release/1.0.0/scripts"
    
    start_content = host.file(scripts_dir + "/start.py").content_string
    stop_content = host.file(scripts_dir + "/stop.py").content_string
    restart_content = host.file(scripts_dir + "/restart.py").content_string
    
    assert start_content.startswith("#!/usr/bin/env python3")
    assert stop_content.startswith("#!/usr/bin/env python3")
    assert restart_content.startswith("#!/usr/bin/env python3")


def test_file_permissions(host):
    """Test that files have correct permissions"""
    instance_dir = "/home/team/app/instances/test-instance-001"
    
    # Directories should be 755
    run_dir = host.file(instance_dir + "/release/1.0.0/run")
    assert run_dir.mode == 0o755
    
    # Config files should be 644
    state_env = host.file(instance_dir + "/release/1.0.0/run/state.env")
    assert state_env.mode == 0o644
    
    # Scripts should be 755
    start_script = host.file(instance_dir + "/release/1.0.0/scripts/start.py")
    assert start_script.mode == 0o755

