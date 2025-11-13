#!/usr/bin/env python3
"""
Ansible action plugin for loading and managing Neuron configuration.
Handles variable precedence, validation, and cross-role variable sharing.
"""

from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError
import yaml
import os
import json


class ActionModule(ActionBase):
    """Load and merge Neuron configuration with proper precedence."""

    def run(self, tmp=None, task_vars=None):
        """Execute the config loading action."""
        if task_vars is None:
            task_vars = {}

        result = super(ActionModule, self).run(tmp, task_vars)
        result['changed'] = False
        result['failed'] = False

        # Get parameters
        config_file = self._task.args.get('config_file', None)
        set_vars = self._task.args.get('set_vars', True)
        validate = self._task.args.get('validate', True)
        cacheable = self._task.args.get('cacheable', True)

        try:
            # Load config from file if provided
            loaded_config = {}
            if config_file:
                config_path = self._find_needle('files', config_file)
                with open(config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f) or {}

            # Merge with existing variables (config file has lower precedence)
            # Variable precedence: task_vars > loaded_config
            merged_config = self._deep_merge(loaded_config.copy(), task_vars)

            # Extract common deployment variables
            deployment_config = self._extract_deployment_config(merged_config, task_vars)

            # Validate if requested
            if validate:
                validation_result = self._validate_config(deployment_config)
                if not validation_result['valid']:
                    result['failed'] = True
                    result['msg'] = f"Configuration validation failed: {', '.join(validation_result['errors'])}"
                    return result
                if validation_result['warnings']:
                    result['warnings'] = validation_result['warnings']

            # Set variables if requested
            if set_vars:
                for key, value in deployment_config.items():
                    if cacheable:
                        self._task.set_variable(key, value, cacheable=True)
                    else:
                        self._task.set_variable(key, value)

            result['config'] = deployment_config
            result['msg'] = "Configuration loaded successfully"

        except Exception as e:
            result['failed'] = True
            result['msg'] = f"Error loading configuration: {str(e)}"

        return result

    def _deep_merge(self, base, override):
        """Deep merge two dictionaries, with override taking precedence."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _extract_deployment_config(self, config, task_vars=None):
        """Extract and normalize deployment configuration."""
        if task_vars is None:
            task_vars = {}
        
        # Get neuron_config for path construction
        neuron_config_obj = config.get('neuron_config', {})
        
        # Get environment home (from ansible_env or default)
        # Try ansible_env first (set by gather_facts)
        ansible_env = task_vars.get('ansible_env', {})
        if 'HOME' in ansible_env:
            env_home = ansible_env['HOME']
        elif 'HOME' in os.environ:
            env_home = os.environ['HOME']
        else:
            env_home = os.path.expanduser('~')
        
        # Get deployment type from neuron_config (default: 'app')
        deployment_type = neuron_config_obj.get('deployment_type', 'app')
        
        # Get team and app from neuron_config
        team = neuron_config_obj.get('team', '')
        app = neuron_config_obj.get('app', neuron_config_obj.get('app_name', ''))
        
        # Instance configuration
        instance_fqn = config.get('NEURON_APP_INSTANCE_FQN', config.get('instance_id'))
        release_version = config.get('release_version', '1.0.0')
        
        # Construct paths based on neuron_config structure
        # Format: env.Home/neuron_config.team/neuron_config.app/releases/version
        #         env.Home/neuron_config.team/neuron_config.app/instances/NEURON_APP_INSTANCE_FQN
        
        deployment = {
            # Instance configuration
            'NEURON_APP_INSTANCE_FQN': instance_fqn,
            'release_version': release_version,
            'instance_user': config.get('instance_user'),
            'instance_group': config.get('instance_group'),
            
            # Deployment type and neuron_config values
            'neuron_deployment_type': deployment_type,
            'neuron_team': team,
            'neuron_app': app,
            
            # Construct paths (will be set below)
            '_neuron_deployment_root': None,
            '_neuron_release_dir_path': None,
            '_neuron_instance_dir': None,
        }
        
        # Construct deployment root: env.Home/team/app (or tools/artifacts)
        if team and app:
            deployment['_neuron_deployment_root'] = os.path.join(
                env_home,
                team,
                app,
                deployment_type  # 'app', 'tools', or 'artifacts'
            )
            
            # Construct release directory path: .../releases/version
            deployment['_neuron_release_dir_path'] = os.path.join(
                deployment['_neuron_deployment_root'],
                'releases',
                release_version
            )
            
            # Construct instance directory: .../instances/NEURON_APP_INSTANCE_FQN
            if instance_fqn:
                deployment['_neuron_instance_dir'] = os.path.join(
                    deployment['_neuron_deployment_root'],
                    'instances',
                    instance_fqn
                )
        
        # Fallback to old-style paths if neuron_config not fully set
        if not deployment['_neuron_deployment_root']:
            # Use old-style deployment root if provided, otherwise construct from defaults
            old_deployment_root = config.get('neuron_deployment_root', os.path.join(env_home, 'team', 'app'))
            old_instance_base = config.get('neuron_instance_base', 'instances')
            old_release_base = config.get('neuron_release_base', 'release')
            
            deployment['_neuron_deployment_root'] = old_deployment_root
            
            if instance_fqn:
                deployment['_neuron_instance_dir'] = os.path.join(
                    old_deployment_root,
                    old_instance_base,
                    instance_fqn
                )
                deployment['_neuron_release_dir_path'] = os.path.join(
                    deployment['_neuron_instance_dir'],
                    old_release_base,
                    release_version
                )
        
        # Set backward compatibility variables
        deployment['neuron_deployment_root'] = deployment['_neuron_deployment_root']
        deployment['neuron_instance_base'] = 'instances'
        deployment['neuron_release_base'] = 'releases'

        # Handle configuration objects with deep merge
        # These need to be merged from defaults -> group_vars -> host_vars -> playbook -> extra_vars
        
        # neuron_features - merge if exists
        if 'neuron_features' in config:
            deployment['neuron_features'] = config['neuron_features']
        
        # neuron_cls_java - deep merge with defaults
        if 'neuron_cls_java' in config:
            deployment['neuron_cls_java'] = config['neuron_cls_java']
        
        # neuron_config - merge if exists
        if 'neuron_config' in config:
            deployment['neuron_config'] = config['neuron_config']
        
        # artifact_source - merge if exists
        if 'artifact_source' in config:
            deployment['artifact_source'] = config['artifact_source']
        
        # Environment variables (ENV_*, ENVSTRIP_*, BEDROCK_*)
        # These are collected from hostvars, so preserve them
        env_vars = {k: v for k, v in config.items() 
                   if k.startswith('ENV_') or k.startswith('ENVSTRIP_') or k.startswith('BEDROCK_')}
        deployment.update(env_vars)

        # Merge all other variables (preserve everything else)
        deployment.update({k: v for k, v in config.items() 
                          if k not in deployment and not k.startswith('_')})

        return deployment

    def _validate_config(self, config):
        """Validate configuration."""
        errors = []
        warnings = []

        # Validate required variables
        if not config.get('NEURON_APP_INSTANCE_FQN') and not config.get('instance_id'):
            errors.append('NEURON_APP_INSTANCE_FQN or instance_id is required')

        if not config.get('release_version'):
            warnings.append('release_version not set, using default')

        # Validate neuron_config for path construction
        neuron_config_obj = config.get('neuron_config', {})
        if neuron_config_obj:
            # If using neuron_config-based paths, validate required fields
            if neuron_config_obj.get('team') and neuron_config_obj.get('app'):
                # Using new-style paths, validate deployment_type if set
                deployment_type = neuron_config_obj.get('deployment_type', 'app')
                if deployment_type not in ['app', 'tools', 'artifacts']:
                    errors.append(f'neuron_config.deployment_type must be one of: app, tools, artifacts (got: {deployment_type})')
        
        # Validate paths (check constructed paths)
        deployment_root = config.get('_neuron_deployment_root') or config.get('neuron_deployment_root')
        if deployment_root and not os.path.isabs(deployment_root):
            errors.append(f'Deployment root must be an absolute path: {deployment_root}')

        # Validate neuron_cls_java if CLS is enabled
        neuron_features = config.get('neuron_features', {})
        if neuron_features.get('cls'):
            cls_java = config.get('neuron_cls_java', {})
            if not cls_java:
                errors.append('neuron_cls_java is required when neuron_features.cls is true')
            elif not cls_java.get('main_class'):
                errors.append('neuron_cls_java.main_class is required when CLS is enabled')
            if not cls_java.get('java_home'):
                warnings.append('neuron_cls_java.java_home not set, using default')

        # Validate artifact_source if configured
        artifact_source = config.get('artifact_source', {})
        if artifact_source:
            source_type = artifact_source.get('type')
            if source_type == 'local':
                local_config = artifact_source.get('local', {})
                neuron_config = config.get('neuron_config', {})
                if not local_config.get('domain'):
                    errors.append('artifact_source.local.domain is required for local source')
                if not local_config.get('app_name') and not neuron_config.get('app_name'):
                    errors.append('artifact_source.local.app_name or neuron_config.app_name is required for local source')
            elif source_type == 'nexus':
                nexus_config = artifact_source.get('nexus', {})
                if not nexus_config.get('url'):
                    errors.append('artifact_source.nexus.url is required for nexus source')
                if not nexus_config.get('artifact_id'):
                    errors.append('artifact_source.nexus.artifact_id is required for nexus source')

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

