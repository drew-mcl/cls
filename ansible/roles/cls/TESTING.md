# Testing Guide for CLS Role

This document describes how to test the CLS Ansible role to ensure it's production-ready and safe.

## Test Types

### 1. Molecule Integration Tests

Molecule provides integration testing using Docker containers.

**Prerequisites:**
```bash
pip install molecule molecule-docker testinfra docker
```

**Run tests:**
```bash
cd ansible/roles/cls
molecule test
```

**Run specific scenario:**
```bash
molecule test -s default
```

**Test what's covered:**
- Directory structure creation
- Script generation and permissions
- Configuration file generation
- Environment variable processing
- Symlink creation
- File permissions
- Python syntax validation

### 2. Safety Tests

Security and safety validation tests.

**Run safety tests:**
```bash
cd ansible/roles/cls
python3 -m pytest tests/integration/test_safety.py -v
```

**What's tested:**
- No hardcoded secrets
- No dangerous shell commands
- Path traversal protection
- Input validation
- File permission safety

### 3. Syntax Tests

Validates YAML and Python syntax.

**Run syntax tests:**
```bash
cd ansible/roles/cls
python3 -m pytest tests/test_ansible_role.py -v
```

**What's tested:**
- YAML syntax validity
- Template file existence
- Python script syntax

### 4. Manual Testing

#### Test Role Application

```bash
# Create test inventory
cat > test-inventory.yml <<EOF
all:
  hosts:
    test-host:
      neuron_features:
        cls: true
      neuron_cls_java:
        main_class: "com.example.Main"
        mem:
          xs: "128m"
          xm: "256m"
        java_home: "/usr/lib/jvm/java-8-openjdk"
      instance_id: "test-001"
      release_version: "1.0.0"
      ENV_TEST: "value"
EOF

# Run playbook
ansible-playbook -i test-inventory.yml test-playbook.yml
```

#### Test Scripts Manually

```bash
# Test start script
./scripts/start.py

# Check status
ps aux | grep java

# Test stop script
./scripts/stop.py

# Test restart script
./scripts/restart.py
```

## Test Checklist

### Pre-Deployment Checklist

- [ ] All Molecule tests pass
- [ ] Safety tests pass
- [ ] Syntax tests pass
- [ ] Manual testing completed
- [ ] No hardcoded secrets
- [ ] File permissions correct
- [ ] Scripts are executable
- [ ] Configuration files generated correctly
- [ ] Environment variables processed correctly
- [ ] Symlinks created correctly

### Production Readiness Checklist

- [ ] Error handling tested
- [ ] Lock file mechanism tested
- [ ] Process verification tested
- [ ] Log rotation tested
- [ ] Disk space checks tested
- [ ] Java version validation tested
- [ ] Hook scripts tested
- [ ] Custom script overwrites tested
- [ ] Rollback tested
- [ ] Concurrent start prevention tested

## Running All Tests

```bash
# Run all tests
cd ansible/roles/cls
molecule test && \
python3 -m pytest tests/ -v && \
ansible-lint . && \
yamllint .
```

## CI/CD Integration

Tests are automatically run on:
- Push to main/develop branches
- Merge requests

### GitLab CI/CD

See `.gitlab-ci.yml` for GitLab CI/CD configuration.

**Stages:**
- `lint` - YAML and Ansible linting
- `test` - Molecule integration tests and safety tests
- `validate` - Syntax validation

**Run locally with GitLab Runner:**
```bash
gitlab-runner exec docker yamllint
gitlab-runner exec docker molecule-test
```

### GitHub Actions

See `.github/workflows/test.yml` for GitHub Actions configuration (if using GitHub).

## Troubleshooting Tests

### Molecule Issues

If Docker issues occur:
```bash
# Check Docker is running
docker ps

# Clean up molecule instances
molecule destroy

# Recreate
molecule create
```

### Test Failures

1. Check test output for specific failures
2. Review test files for expected behavior
3. Verify test environment matches production
4. Check file permissions and ownership

## Adding New Tests

### Add Molecule Test

Edit `molecule/default/tests/test_default.py`:
```python
def test_new_feature(host):
    """Test new feature"""
    assert host.file("/path/to/file").exists
```

### Add Safety Test

Edit `tests/integration/test_safety.py`:
```python
def test_new_safety_check():
    """Test new safety check"""
    # Your test code
```

## Test Coverage Goals

- **Unit Tests**: 80%+ coverage
- **Integration Tests**: All critical paths
- **Safety Tests**: All security concerns
- **Manual Tests**: All user-facing features

