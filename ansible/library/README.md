# Neuron Ansible Library

This directory contains custom Ansible modules and utilities.

## config_parser.py

A Python script that parses Ansible inventory configuration and determines which roles should be enabled.

### Usage

```bash
python3 library/config_parser.py inventory.yml [host]
```

### Output

The script outputs JSON with:
- `enabled_roles`: List of roles that should be enabled
- `validation`: Validation results with errors and warnings
- `config_summary`: Summary of configuration

### Example

```bash
$ python3 library/config_parser.py example-inventory.yml app-server-01
{
  "enabled_roles": [
    "artifact",
    "cls"
  ],
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": []
  },
  "config_summary": {
    "roles": ["artifact", "cls"],
    "instance_id": "my-app-001",
    "release_version": "1.0.0",
    "artifact": {
      "domain": "me",
      "app_name": "my-app"
    },
    "cls": {
      "main_class": "com.example.MainClass",
      "java_home": "/usr/lib/jvm/java-8-openjdk"
    }
  }
}
```

### Integration

The config parser can be used in CI/CD pipelines to validate configuration before deployment:

```bash
if ! python3 library/config_parser.py inventory.yml; then
  echo "Configuration validation failed"
  exit 1
fi
```

