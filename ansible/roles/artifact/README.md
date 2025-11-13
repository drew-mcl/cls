# Artifact Ansible Role

This Ansible role fetches and extracts artifacts from multiple sources: local/runner repositories or Nexus repositories.

## Features

- **Multiple Artifact Sources**: Supports local/runner artifacts and Nexus repositories
- **Local/CI Support**: Works both locally and in GitLab CI environments for local artifacts
- **Nexus Integration**: Uses `community.general.maven_nexus` module for Nexus artifacts
- **Auto-detection**: Automatically detects repository root from playbook location or CI_PROJECT_DIR (local source)
- **Extraction**: Extracts artifacts to the release directory with proper permissions

## Requirements

- Ansible 2.9+
- For Nexus source: `community.general` collection must be installed
- For local source: `artifact_source.local.domain` and `artifact_source.local.app_name` must be set
- For Nexus source: `artifact_source.nexus.url`, `artifact_source.nexus.group_id`, and `artifact_source.nexus.artifact_id` must be set

## Role Variables

### Artifact Source Configuration

The role supports two artifact source types:

#### Local/Runner Source

Used for local development and GitLab CI runners:

```yaml
artifact_source:
  type: "local"
  local:
    domain: "me"      # Domain/org name (e.g., "me", "sor", "xyz")
    app_name: "my-app"  # App name matching {domain}/apps/{app_name} structure
    base_path: "{{ ansible_env.CI_PROJECT_DIR | default(...) }}"  # Optional: override base path
```

#### Nexus Source

Used for fetching artifacts from Nexus repositories:

```yaml
artifact_source:
  type: "nexus"
  nexus:
    url: "https://nexus.example.com"  # Nexus repository URL
    group_id: "com.example"           # Maven groupId
    artifact_id: "my-app"             # Maven artifactId
    version: "1.0.0"                   # Artifact version (or use release_version)
    repository: "maven-releases"       # Nexus repository name
    username: "user"                   # Optional: Nexus username
    password: "pass"                    # Optional: Nexus password (use vault)
    extension: "tgz"                   # Artifact extension (default: tgz)
    classifier: null                   # Optional: Maven classifier
```

### Common Variables

```yaml
instance_id: "my-app-001"
release_version: "1.0.0"  # Used as default version for Nexus if not specified

# Optional overrides
instance_dir: "/home/team/app/instances/{{ instance_id }}"
instance_user: "appuser"
instance_group: "appgroup"
```

## Usage

### Local Source Example

```yaml
- hosts: app_servers
  roles:
    - artifact
  vars:
    artifact_source:
      type: "local"
      local:
        domain: "me"
        app_name: "my-app"
    instance_id: "my-app-001"
    release_version: "1.0.0"
```

### Nexus Source Example

```yaml
- hosts: app_servers
  roles:
    - artifact
  vars:
    artifact_source:
      type: "nexus"
      nexus:
        url: "https://nexus.example.com"
        group_id: "com.example"
        artifact_id: "my-app"
        version: "{{ release_version }}"
        repository: "maven-releases"
        username: "{{ nexus_username }}"
        password: "{{ nexus_password }}"  # Use vault
    instance_id: "my-app-001"
    release_version: "1.0.0"
```

## Artifact Path Structure

### Local Source

The role expects artifacts at:
```
{base_path}/{domain}/apps/{app_name}/build/distribution/*.tgz
```

Where:
- `base_path` defaults to `CI_PROJECT_DIR` (GitLab CI) or detected from `playbook_dir` (local)
- `domain` comes from `artifact_source.local.domain`
- `app_name` comes from `artifact_source.local.app_name`

### Nexus Source

The role downloads artifacts using Maven coordinates:
- `groupId`: `artifact_source.nexus.group_id`
- `artifactId`: `artifact_source.nexus.artifact_id`
- `version`: `artifact_source.nexus.version` or `release_version`
- `extension`: `artifact_source.nexus.extension` (default: `tgz`)
- `classifier`: `artifact_source.nexus.classifier` (optional)

## Dependencies

- For Nexus source: `community.general` collection
  ```bash
  ansible-galaxy collection install community.general
  ```

## License

See main repository license

