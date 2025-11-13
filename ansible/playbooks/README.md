# Neuron Deployment Playbooks

This directory contains common playbooks for deploying Neuron applications.

## deploy.yml

The main deployment playbook that automatically determines which roles to run based on configuration.

### Usage

```bash
ansible-playbook -i inventory.yml playbooks/deploy.yml
```

### How It Works

The playbook automatically detects which roles should be enabled:

1. **Artifact Role**: Enabled when `neuron_config.app_name` and `neuron_config.domain` are set
2. **CLS Role**: Enabled when `neuron_features.cls` is `true`

### Example Inventory

```yaml
all:
  hosts:
    app-server-01:
      # Enable CLS feature
      neuron_features:
        cls: true
      
      # Artifact configuration
      neuron_config:
        domain: "me"
        app_name: "my-app"
      
      # CLS configuration
      neuron_cls_java:
        main_class: "com.example.MainClass"
        java_home: "/usr/lib/jvm/java-8-openjdk"
      
      # Common configuration
      instance_id: "my-app-001"
      release_version: "1.0.0"
```

### Role Execution Order

1. `artifact` role (if enabled) - fetches and extracts artifacts
2. `cls` role (if enabled) - sets up lifecycle management

The playbook will display which roles are enabled before execution.

