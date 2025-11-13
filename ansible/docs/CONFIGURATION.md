# Configuration Management Guide

This guide explains how to manage configuration in the Neuron Ansible collection using production-ready best practices.

## Configuration Hierarchy

Configuration follows Ansible's variable precedence, with our custom additions:

1. **Role defaults** (lowest precedence) - `roles/*/defaults/main.yml`
2. **Group vars (all)** - `group_vars/all.yml`
3. **Group vars (environment)** - `group_vars/{env}.yml` (e.g., `prod.yml`, `dev.yml`)
4. **Host vars** - `host_vars/{hostname}.yml`
5. **Playbook vars** - Variables defined in playbooks
6. **Extra vars** (highest precedence) - `-e` command line arguments

## Configuration Objects

The collection uses several configuration objects that support deep merging:

### neuron_config

Application-level configuration:

```yaml
neuron_config:
  app_name: "my-app"  # Used by artifact role for local source
```

### neuron_cls_java

CLS Java application configuration:

```yaml
neuron_cls_java:
  main_class: "com.example.MainClass"  # Required
  param_class: "com.example.ParamClass"  # Optional
  mem:
    xs: "256m"  # Initial heap
    xm: "512m"  # Max heap
  java_home: "/usr/lib/jvm/java-8-openjdk"
```

### neuron_features

Feature flags:

```yaml
neuron_features:
  cls: true  # Enable CLS role
```

### artifact_source

Artifact source configuration:

```yaml
artifact_source:
  type: "local"  # or "nexus"
  local:
    domain: "me"
    app_name: "my-app"
  nexus:
    url: "https://nexus.example.com"
    group_id: "com.neuron"
    artifact_id: "my-app"
```

## Deep Merging Configuration Objects

Configuration objects are **deep merged**, meaning you only need to override the keys you want to change.

### Example: Override Only Memory Settings

**In `group_vars/all.yml`:**
```yaml
neuron_cls_java:
  mem:
    xs: "256m"
    xm: "512m"
  java_home: "/usr/lib/jvm/java-8-openjdk"
```

**In `group_vars/prod.yml`:**
```yaml
neuron_cls_java:
  mem:
    xs: "512m"   # Only override xs
    xm: "2048m" # Only override xm
  # java_home not specified, uses value from all.yml
```

**Result:**
```yaml
neuron_cls_java:
  mem:
    xs: "512m"   # From prod.yml
    xm: "2048m" # From prod.yml
  java_home: "/usr/lib/jvm/java-8-openjdk"  # From all.yml
```

## Common Deployment Variables

These variables can be set at any level and will be shared across roles:

### Core Variables

- `neuron_deployment_root` - Base directory for all deployments (default: `/home/team/app`)
- `neuron_instance_base` - Subdirectory for instances (default: `instances`)
- `neuron_release_base` - Subdirectory for releases (default: `release`)
- `NEURON_APP_INSTANCE_FQN` - Fully qualified instance name (required)
- `release_version` - Version to deploy (default: `1.0.0`)

### Constructed Variables (Auto-generated)

These are automatically constructed from the above variables:

- `_neuron_instance_dir` - Full path to instance directory
- `_neuron_release_dir_path` - Full path to release directory

These variables are set with `cacheable: yes` so they're available across all roles.

## Configuration Files

### Global Defaults (`group_vars/all.yml`)

Set defaults that apply to all environments:

```yaml
neuron_deployment_root: "/home/team/app"
neuron_cls_java:
  mem:
    xs: "256m"
    xm: "512m"
```

### Environment-Specific (`group_vars/prod.yml`)

Override for production:

```yaml
neuron_deployment_root: "/opt/neuron/apps"
neuron_cls_java:
  mem:
    xs: "512m"
    xm: "2048m"
```

### Host-Specific (`host_vars/app-server-01.yml`)

Override for specific hosts:

```yaml
NEURON_APP_INSTANCE_FQN: "my-app-prod-001"
release_version: "2.1.0"
neuron_cls_java:
  main_class: "com.example.ProdMainClass"
```

## Using the Config Loader

The `neuron_config` action plugin loads and validates configuration:

```yaml
- name: Load Neuron configuration
  neuron_config:
    config_file: "config/deployment.yml"  # Optional
    set_vars: true
    validate: true
    cacheable: true
```

The plugin:
- Deep merges configuration objects
- Validates required fields
- Constructs paths automatically
- Makes variables cacheable for cross-role use

## Variable Override Examples

### Override Deployment Root

**Via group vars:**
```yaml
# group_vars/prod.yml
neuron_deployment_root: "/opt/neuron/apps"
```

**Via extra vars:**
```bash
ansible-playbook -i inventory.yml playbooks/deploy.yml \
  -e "neuron_deployment_root=/custom/path"
```

### Override Only Part of neuron_cls_java

**Via host vars:**
```yaml
# host_vars/app-server-01.yml
neuron_cls_java:
  main_class: "com.example.CustomMainClass"
  # mem and java_home come from group_vars
```

### Override artifact_source Type

**Via playbook:**
```yaml
- hosts: all
  vars:
    artifact_source:
      type: "nexus"
      nexus:
        url: "https://nexus.example.com"
        artifact_id: "my-app"
```

## Best Practices

### 1. Use Group Vars for Environments

Create environment-specific group vars:

```
group_vars/
├── all.yml          # Global defaults
├── dev.yml         # Development overrides
├── staging.yml     # Staging overrides
└── prod.yml        # Production overrides
```

### 2. Only Override What You Need

Configuration objects are deep merged, so only specify what changes:

```yaml
# ✓ Good - only override what changes
neuron_cls_java:
  mem:
    xm: "2048m"

# ✗ Bad - unnecessary duplication
neuron_cls_java:
  main_class: "com.example.MainClass"  # Already in all.yml
  mem:
    xs: "256m"  # Already in all.yml
    xm: "2048m"
  java_home: "/usr/lib/jvm/java-8-openjdk"  # Already in all.yml
```

### 3. Use Host Vars for Host-Specific Config

```
host_vars/
├── app-server-01.yml
└── app-server-02.yml
```

### 4. Use Extra Vars for One-Time Overrides

```bash
ansible-playbook -i inventory.yml playbooks/deploy.yml \
  -e "release_version=2.2.0" \
  -e "neuron_deployment_root=/tmp/test"
```

### 5. Cacheable Variables

Variables that need to be shared across roles should use `cacheable: yes`:

```yaml
- name: Set shared variable
  set_fact:
    my_shared_var: "value"
  cacheable: yes
```

The `neuron_config` plugin automatically makes configuration objects cacheable.

## Configuration Object Reference

### neuron_cls_java

```yaml
neuron_cls_java:
  main_class: string      # Required when CLS enabled
  param_class: string     # Optional
  mem:
    xs: string           # Initial heap (e.g., "256m")
    xm: string           # Max heap (e.g., "512m")
  java_home: string      # Java home directory
```

### neuron_config

```yaml
neuron_config:
  app_name: string       # Application name (used by artifact role)
```

### artifact_source

```yaml
artifact_source:
  type: "local" | "nexus"
  local:
    domain: string       # Required for local
    app_name: string     # Optional, falls back to neuron_config.app_name
  nexus:
    url: string          # Required for nexus
    group_id: string     # Defaults to "com.neuron"
    artifact_id: string  # Required for nexus
    version: string      # Optional, defaults to release_version
    repository: string   # Defaults to "maven-releases"
    extension: string    # Defaults to "tgz"
```

## Troubleshooting

### Configuration Not Merging Properly

Ensure you're using the `neuron_config` action plugin in your playbook:

```yaml
- name: Load Neuron configuration
  neuron_config:
    set_vars: true
    validate: true
```

### Variables Not Available in Roles

Configuration objects are automatically cached. If you set custom variables, use `cacheable: yes`:

```yaml
- set_fact:
    my_var: "value"
  cacheable: yes
```

### Configuration Not Overriding

Check variable precedence. Use `-e` for highest precedence:

```bash
ansible-playbook -e "neuron_cls_java.mem.xm=2048m" ...
```

### Deep Merge Not Working

Ansible's `combine` filter with `recursive=True` handles deep merging. The `neuron_config` plugin uses this automatically. For manual merging:

```yaml
neuron_cls_java: "{{ neuron_cls_java | default({}) | combine(override, recursive=True) }}"
```
