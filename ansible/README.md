# Neuron Ansible Collection

An Ansible collection for Neuron application deployment and lifecycle management.

## Collection Structure

```
ansible/
├── galaxy.yml              # Collection metadata
├── roles/
│   ├── artifact/           # Artifact fetching role
│   └── cls/                # CLS lifecycle management role
├── playbooks/
│   └── deploy.yml          # Common deployment playbook
├── library/
│   └── config_parser.py    # Configuration parser utility
└── example-inventory.yml   # Example inventory file
```

## Roles

### artifact

Fetches and extracts artifacts from multiple sources: local/runner repositories or Nexus repositories.

**Enabled when**: 
- Local source: `artifact_source.type == 'local'` and `artifact_source.local.domain` and `artifact_source.local.app_name` are set
- Nexus source: `artifact_source.type == 'nexus'` and `artifact_source.nexus.url`, `artifact_source.nexus.group_id`, and `artifact_source.nexus.artifact_id` are set

**Features**:
- Multiple artifact sources: local/runner or Nexus
- Automatic artifact discovery from `{domain}/apps/{app_name}/build/distribution/` (local)
- Nexus integration using `community.general.maven_nexus` module
- Works locally and in GitLab CI
- Auto-detects repository root (local source)

See [roles/artifact/README.md](roles/artifact/README.md) for details.

### cls

Sets up lifecycle management scripts and configuration for Java applications.

**Enabled when**: `neuron_features.cls` is `true`

**Features**:
- Generates lifecycle scripts (start, stop, restart)
- Manages environment variables
- JVM configuration
- Release management

See [roles/cls/README.md](roles/cls/README.md) for details.

## Usage

### Common Playbook (Recommended)

Use the common playbook which automatically determines which roles to run:

```bash
ansible-playbook -i inventory.yml playbooks/deploy.yml
```

The playbook will:
1. Parse your inventory configuration
2. Determine which roles should be enabled
3. Display enabled roles
4. Execute only the necessary roles

### Manual Role Inclusion

You can also include roles manually in your playbook:

```yaml
- hosts: all
  become: yes
  roles:
    - role: artifact
      when: >
        (artifact_source.type == 'local' and artifact_source.local.domain is defined and artifact_source.local.app_name is defined) or
        (artifact_source.type == 'nexus' and artifact_source.nexus.url is defined and artifact_source.nexus.group_id is defined and artifact_source.nexus.artifact_id is defined)
    - role: cls
      when: neuron_features.cls is defined and neuron_features.cls | bool
```

## Configuration

### Example Inventory

```yaml
all:
  hosts:
    app-server-01:
      # Enable CLS feature
      neuron_features:
        cls: true
      
      # Artifact configuration (enables artifact role)
      # Example 1: Local/runner source
      artifact_source:
        type: "local"
        local:
          domain: "me"      # e.g., "me", "sor", "xyz"
          app_name: "my-app"
      
      # Example 2: Nexus source
      # artifact_source:
      #   type: "nexus"
      #   nexus:
      #     url: "https://nexus.example.com"
      #     group_id: "com.example"
      #     artifact_id: "my-app"
      #     version: "{{ release_version }}"
      #     repository: "maven-releases"
      
      # CLS Java configuration
      neuron_cls_java:
        main_class: "com.example.MainClass"
        param_class: "com.example.ParamClass"  # Optional
        mem:
          xs: "256m"
          xm: "512m"
        java_home: "/usr/lib/jvm/java-8-openjdk"
      
      # Common configuration
      instance_id: "my-app-001"
      instance_dir: "/home/team/app/instances/my-app-001"
      release_version: "1.0.0"
      instance_user: "appuser"
      instance_group: "appgroup"
      
      # Environment variables
      ENV_DATABASE_URL: "postgresql://localhost:5432/mydb"
      ENVSTRIP_API_KEY: "secret-key-123"
      BEDROCK_CONFIG_PATH: "/etc/bedrock/config"
```

## Configuration Parser

The collection includes a configuration parser utility that validates your inventory and determines which roles should be enabled:

```bash
python3 library/config_parser.py inventory.yml [host]
```

**Output**:
- List of enabled roles
- Configuration validation (errors and warnings)
- Configuration summary

**Example**:
```bash
$ python3 library/config_parser.py example-inventory.yml app-server-01
{
  "enabled_roles": ["artifact", "cls"],
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": []
  },
  "config_summary": {
    "roles": ["artifact", "cls"],
    "instance_id": "my-app-001",
    ...
  }
}
```

## Role Detection Logic

### Artifact Role

Enabled when:
- **Local source**: `artifact_source.type == 'local'` and `artifact_source.local.domain` and `artifact_source.local.app_name` are set
- **Nexus source**: `artifact_source.type == 'nexus'` and `artifact_source.nexus.url`, `artifact_source.nexus.group_id`, and `artifact_source.nexus.artifact_id` are set

### CLS Role

Enabled when:
- `neuron_features.cls` is defined and `true`

## Installation

### As a Collection

```bash
ansible-galaxy collection build
ansible-galaxy collection install neuron-cls-1.0.0.tar.gz
```

### Direct Usage

If using directly from the repository:

```bash
# Set ANSIBLE_ROLES_PATH to include roles directory
export ANSIBLE_ROLES_PATH=/path/to/ansible/roles:$ANSIBLE_ROLES_PATH

# Use playbooks directly
ansible-playbook -i inventory.yml playbooks/deploy.yml
```

## Requirements

- Ansible 2.9+
- Python 3.6+ (for config parser)
- PyYAML (for config parser)

## License

MIT

