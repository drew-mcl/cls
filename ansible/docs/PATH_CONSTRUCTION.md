# Path Construction Guide

This guide explains how paths are constructed from `neuron_config` in the Neuron Ansible collection.

## Path Construction Logic

Paths are automatically constructed by the `neuron_config` action plugin based on the `neuron_config` object structure.

### New Style (neuron_config-based)

When `neuron_config.team` and `neuron_config.app` are set, paths are constructed as:

```
env.Home/neuron_config.team/neuron_config.app/deployment_type/releases/version
env.Home/neuron_config.team/neuron_config.app/deployment_type/instances/NEURON_APP_INSTANCE_FQN
```

**Example:**
```yaml
neuron_config:
  team: "engineering"
  app: "my-app"
  deployment_type: "app"  # or "tools", "artifacts"

NEURON_APP_INSTANCE_FQN: "my-app-prod-001"
release_version: "1.2.3"
```

**Resulting paths:**
- Deployment root: `/home/user/engineering/my-app/app`
- Release dir: `/home/user/engineering/my-app/app/releases/1.2.3`
- Instance dir: `/home/user/engineering/my-app/app/instances/my-app-prod-001`

### Deployment Types

The `deployment_type` in `neuron_config` determines the subdirectory:

- `app` (default) - Standard application deployments
- `tools` - Tool deployments
- `artifacts` - Artifact deployments

**Example with tools:**
```yaml
neuron_config:
  team: "engineering"
  app: "deployment-tool"
  deployment_type: "tools"
```

**Resulting paths:**
- Deployment root: `/home/user/engineering/deployment-tool/tools`
- Release dir: `/home/user/engineering/deployment-tool/tools/releases/1.0.0`
- Instance dir: `/home/user/engineering/deployment-tool/tools/instances/tool-instance-001`

### Fallback (Old Style)

If `neuron_config.team` or `neuron_config.app` are not set, the plugin falls back to old-style paths:

```
neuron_deployment_root/instances/NEURON_APP_INSTANCE_FQN
neuron_deployment_root/instances/NEURON_APP_INSTANCE_FQN/release/version
```

## Configuration

### Required Fields

For new-style paths:
- `neuron_config.team` - Team name
- `neuron_config.app` or `neuron_config.app_name` - Application name

### Optional Fields

- `neuron_config.deployment_type` - Deployment type (default: `"app"`)
- `NEURON_APP_INSTANCE_FQN` - Instance identifier
- `release_version` - Release version (default: `"1.0.0"`)

### Environment Home

The `env.Home` is determined from:
1. `ansible_env.HOME` (if available)
2. `$HOME` environment variable
3. `os.path.expanduser('~')` as fallback

## Examples

### Basic Application Deployment

```yaml
neuron_config:
  team: "platform"
  app: "api-service"
  deployment_type: "app"  # default

NEURON_APP_INSTANCE_FQN: "api-prod-001"
release_version: "2.1.0"
```

**Paths:**
- `/home/user/platform/api-service/app/releases/2.1.0`
- `/home/user/platform/api-service/app/instances/api-prod-001`

### Tools Deployment

```yaml
neuron_config:
  team: "devops"
  app: "deployment-script"
  deployment_type: "tools"

NEURON_APP_INSTANCE_FQN: "deploy-script-001"
release_version: "1.0.0"
```

**Paths:**
- `/home/user/devops/deployment-script/tools/releases/1.0.0`
- `/home/user/devops/deployment-script/tools/instances/deploy-script-001`

### Artifacts Deployment

```yaml
neuron_config:
  team: "build"
  app: "artifact-storage"
  deployment_type: "artifacts"

NEURON_APP_INSTANCE_FQN: "artifacts-001"
release_version: "1.0.0"
```

**Paths:**
- `/home/user/build/artifact-storage/artifacts/releases/1.0.0`
- `/home/user/build/artifact-storage/artifacts/instances/artifacts-001`

## Generated Variables

The `neuron_config` action plugin sets these variables:

- `_neuron_deployment_root` - Base deployment directory
- `_neuron_release_dir_path` - Release directory path
- `_neuron_instance_dir` - Instance directory path
- `neuron_deployment_type` - Deployment type (app/tools/artifacts)
- `neuron_team` - Team name
- `neuron_app` - App name

All variables are set with `cacheable: yes` so they're available across all roles.

## Best Practices

1. **Set neuron_config at group level:**
   ```yaml
   # group_vars/prod.yml
   neuron_config:
     team: "platform"
     app: "my-app"
   ```

2. **Override deployment_type per host if needed:**
   ```yaml
   # host_vars/tool-server.yml
   neuron_config:
     deployment_type: "tools"
   ```

3. **Use app_name for artifact role compatibility:**
   ```yaml
   neuron_config:
     app: "my-app"
     app_name: "my-app"  # Used by artifact role
   ```

## Migration

### From Old Style

**Old:**
```yaml
neuron_deployment_root: "/home/team/app"
instance_dir: "/home/team/app/instances/my-app-001"
```

**New:**
```yaml
neuron_config:
  team: "team"
  app: "app"
NEURON_APP_INSTANCE_FQN: "my-app-001"
```

Paths are automatically constructed from `neuron_config`.

