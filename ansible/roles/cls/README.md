# CLS Ansible Role

This Ansible role generates lifecycle management scripts and configuration files for Java applications using the CLS (Common Lifecycle Service) pattern.

## Features

- **Automatic Script Generation**: Creates Python 3.6-compatible lifecycle scripts for Java applications
- **Environment Variable Management**: Collects and manages environment variables from inventory
- **Release Management**: Integrates with release-based deployment structure
- **JVM Configuration**: Generates JVM arguments file from inventory variables
- **Pre-flight Validation**: Validates configuration and prerequisites before deployment
- **Status Monitoring**: Comprehensive status script for health checks
- **Fault Tolerance**: Robust error handling, lock files, and process verification
- **Log Management**: Automatic log rotation and management

## Directory Structure

The role creates and manages the following directory structure:

```
home/team/app/instances/instance_id/
├── run/              # Runtime files (symlinked to current/run)
├── data/             # Data directory
├── current/          # Symlink to current release
├── previous/         # Symlink to previous release (manual rollback)
├── log/              # Application logs
├── scripts/          # Scripts directory (symlinked to current/scripts)
└── release/
    └── release.x.y.z/
        ├── run/
        │   ├── state.env
        │   └── jvm.args
        ├── scripts/
        │   ├── start.py
        │   ├── stop.py
        │   └── restart.py
        └── cls/                     # CLS customizations (from dist/cls/ in repo)
            ├── hooks.d/             # Custom hook scripts
            │   ├── pre-start.sh
            │   ├── post-start.sh
            │   ├── pre-stop.sh
            │   └── post-stop.sh
            ├── scripts/            # Custom script overwrites
            │   ├── start.py        # Overwrites generated start.py
            │   └── stop.py         # Overwrites generated stop.py
            └── *.args              # Additional JVM args files
```

### Custom Scripts and Hooks

In your Gradle repository, place files in `dist/cls/` and they will be included in the distribution. On the host, these files will be at `release/release.x.y.z/cls/`:

- **Custom Scripts**: Place `start.py` or `stop.py` in `dist/cls/scripts/` in your repo to completely override the generated scripts
- **Hook Scripts**: Place bash scripts in `dist/cls/hooks.d/` in your repo:
  - `pre-start.sh` - Runs before application starts
  - `post-start.sh` - Runs after successful start
  - `pre-stop.sh` - Runs before application stops
  - `post-stop.sh` - Runs after application stops
- **Additional JVM Args**: Place any `.args` file in `dist/cls/` in your repo to append additional JVM arguments

**Note**: Files are picked up at runtime from the deployed distribution on the host, not during Ansible execution.

## Inventory Variables

### Required Variables

```yaml
neuron_features:
  cls: true

neuron_cls_java:
  main_class: "com.example.MainClass"  # Required
  param_class: "com.example.ParamClass"  # Optional
  mem:
    xs: "256m"  # Initial heap size
    xm: "512m"  # Maximum heap size
  java_home: "/usr/lib/jvm/java-8-openjdk"  # Java home directory
```

### Environment Variables

The role automatically collects variables prefixed with:
- `ENV_*` - Added to state.env with prefix
- `ENVSTRIP_*` - Added to state.env without prefix (prefix is removed)
- `BEDROCK_*` - Added to state.env with prefix

Example:

```yaml
ENV_DATABASE_URL: "postgresql://localhost:5432/mydb"
ENVSTRIP_API_KEY: "secret-key-123"  # Will be stored as API_KEY=secret-key-123
BEDROCK_CONFIG_PATH: "/etc/bedrock/config"
```

### Instance Configuration

```yaml
instance_id: "my-app-001"
instance_dir: "/home/team/app/instances/{{ instance_id }}"
release_version: "1.2.3"
instance_user: "appuser"
instance_group: "appgroup"
```

## Usage

### Basic Playbook

```yaml
---
- hosts: app_servers
  roles:
    - role: cls
      vars:
        instance_id: "my-app-001"
        release_version: "1.2.3"
        neuron_features:
          cls: true
        neuron_cls_java:
          main_class: "com.example.MainClass"
          param_class: "com.example.ParamClass"
          mem:
            xs: "512m"
            xm: "1024m"
          java_home: "/usr/lib/jvm/java-11-openjdk"
        ENV_DATABASE_URL: "postgresql://localhost:5432/mydb"
        ENVSTRIP_API_KEY: "secret-key-123"
        BEDROCK_CONFIG_PATH: "/etc/bedrock/config"
```

### Inventory Example

```yaml
---
all:
  hosts:
    app-server-01:
      neuron_features:
        cls: true
      neuron_cls_java:
        main_class: "com.example.MainClass"
        param_class: "com.example.ParamClass"
        mem:
          xs: "256m"
          xm: "512m"
        java_home: "/usr/lib/jvm/java-8-openjdk"
      instance_id: "my-app-001"
      release_version: "1.0.0"
      ENV_DATABASE_URL: "postgresql://localhost:5432/mydb"
      ENVSTRIP_API_KEY: "secret-key-123"
      BEDROCK_CONFIG_PATH: "/etc/bedrock/config"
```

## Generated Files

### start.py

The Python start script:
- Runs `pre-start.sh` hook if it exists
- Checks if the application is already running
- Sources `state.env` for environment variables
- Reads JVM arguments from `jvm.args` and any `.args` files in `cls/` directory
- Builds classpath by collecting all `.jar` files from `lib/` directory
- Starts the Java application in the background
- Creates a PID file for process management
- Runs `post-start.sh` hook if it exists

### stop.py

The Python stop script:
- Runs `pre-stop.sh` hook if it exists
- Reads the PID from the PID file
- Sends SIGTERM for graceful shutdown
- Falls back to SIGKILL if needed
- Removes the PID file after shutdown
- Runs `post-stop.sh` hook if it exists

### restart.py

Convenience script that performs a stop followed by a start:
- Stops the application gracefully
- Waits briefly
- Starts the application
- Provides clear status messages

Usage:
```bash
./scripts/restart.py
```

### state.env

Contains all environment variables collected from inventory:
- Variables prefixed with `ENV_` or `BEDROCK_` (with prefix)
- Variables prefixed with `ENVSTRIP_` (without prefix)

### jvm.args

Contains base JVM arguments based on memory settings. Additional arguments can be provided via `.args` files in the `cls/` directory (from `dist/cls/` in your repo), which will be appended to the base arguments.

## Release Management

The role integrates with a release-based deployment model:

1. **New Release**: Files are generated in `release/release.x.y.z/`
2. **Symlink Update**: The `current` symlink is updated to point to the new release
3. **Rollback**: Manually swap `current` and `previous` symlinks to rollback

All generated files (scripts, state.env, jvm.args) are stored in the release directory, ensuring that rollbacks restore the complete state including CLS configuration.

## Rollback Process

To rollback to a previous release:

```bash
# On the target server
cd /home/team/app/instances/instance_id
mv current previous_backup
mv previous current
# Or manually:
ln -sfn release/release.x.y.z current
```

The scripts will automatically use the correct release's configuration files.

## Testing

The role includes comprehensive tests to ensure production readiness:

- **Molecule Integration Tests**: Full integration testing with Docker
- **Safety Tests**: Security and safety validation
- **Syntax Tests**: YAML and Python syntax validation

See [TESTING.md](TESTING.md) for detailed testing instructions.

**Quick test:**
```bash
cd ansible/roles/cls
molecule test
```

## Requirements

- Ansible 2.9+
- Python 3.6+ on target hosts
- Java runtime environment
- Bash shell

## Dependencies

None

## License

Proprietary

