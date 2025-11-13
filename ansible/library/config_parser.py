#!/usr/bin/env python3
"""
Configuration parser for Neuron Ansible collection.
Parses inventory configuration and determines which roles should be enabled.
"""

import json
import sys
import yaml
from typing import Dict, List, Set, Any


class ConfigParser:
    """Parse Ansible inventory configuration and determine enabled roles."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize parser with configuration.
        
        Args:
            config: Dictionary containing host variables from Ansible inventory
        """
        self.config = config
        self.enabled_roles: Set[str] = set()
    
    def parse(self) -> Dict[str, Any]:
        """
        Parse configuration and determine enabled roles.
        
        Returns:
            Dictionary with parsing results including enabled roles and validation
        """
        self._check_artifact_role()
        self._check_cls_role()
        
        return {
            'enabled_roles': sorted(list(self.enabled_roles)),
            'validation': self._validate_config(),
            'config_summary': self._get_config_summary()
        }
    
    def _check_artifact_role(self) -> None:
        """Check if artifact role should be enabled."""
        artifact_source = self.config.get('artifact_source', {})
        source_type = artifact_source.get('type')
        
        if source_type == 'local':
            local_config = artifact_source.get('local', {})
            if (local_config.get('domain') and 
                local_config.get('app_name')):
                self.enabled_roles.add('artifact')
        elif source_type == 'nexus':
            nexus_config = artifact_source.get('nexus', {})
            if (nexus_config.get('url') and 
                nexus_config.get('group_id') and 
                nexus_config.get('artifact_id')):
                self.enabled_roles.add('artifact')
    
    def _check_cls_role(self) -> None:
        """Check if cls role should be enabled."""
        neuron_features = self.config.get('neuron_features', {})
        
        if neuron_features.get('cls') is True:
            self.enabled_roles.add('cls')
    
    def _validate_config(self) -> Dict[str, Any]:
        """
        Validate configuration for enabled roles.
        
        Returns:
            Dictionary with validation results
        """
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate artifact role requirements
        if 'artifact' in self.enabled_roles:
            artifact_source = self.config.get('artifact_source', {})
            source_type = artifact_source.get('type')
            
            if source_type == 'local':
                local_config = artifact_source.get('local', {})
                if not local_config.get('app_name'):
                    validation['errors'].append('artifact role (local) requires artifact_source.local.app_name')
                    validation['valid'] = False
                
                if not local_config.get('domain'):
                    validation['errors'].append('artifact role (local) requires artifact_source.local.domain')
                    validation['valid'] = False
            
            elif source_type == 'nexus':
                nexus_config = artifact_source.get('nexus', {})
                if not nexus_config.get('url'):
                    validation['errors'].append('artifact role (nexus) requires artifact_source.nexus.url')
                    validation['valid'] = False
                
                if not nexus_config.get('group_id'):
                    validation['errors'].append('artifact role (nexus) requires artifact_source.nexus.group_id')
                    validation['valid'] = False
                
                if not nexus_config.get('artifact_id'):
                    validation['errors'].append('artifact role (nexus) requires artifact_source.nexus.artifact_id')
                    validation['valid'] = False
            
            if not self.config.get('instance_id'):
                validation['errors'].append('artifact role requires instance_id')
                validation['valid'] = False
            
            if not self.config.get('release_version'):
                validation['warnings'].append('release_version not set, using default')
        
        # Validate cls role requirements
        if 'cls' in self.enabled_roles:
            if not self.config.get('neuron_cls_java'):
                validation['errors'].append('cls role requires neuron_cls_java')
                validation['valid'] = False
            else:
                cls_java = self.config.get('neuron_cls_java', {})
                if not cls_java.get('main_class'):
                    validation['errors'].append('cls role requires neuron_cls_java.main_class')
                    validation['valid'] = False
                
                if not cls_java.get('java_home'):
                    validation['warnings'].append('neuron_cls_java.java_home not set, using default')
            
            if not self.config.get('instance_id'):
                validation['errors'].append('cls role requires instance_id')
                validation['valid'] = False
            
            if not self.config.get('release_version'):
                validation['warnings'].append('release_version not set, using default')
        
        return validation
    
    def _get_config_summary(self) -> Dict[str, Any]:
        """
        Get summary of configuration.
        
        Returns:
            Dictionary with configuration summary
        """
        summary = {
            'roles': sorted(list(self.enabled_roles)),
            'instance_id': self.config.get('instance_id'),
            'release_version': self.config.get('release_version', '1.0.0'),
        }
        
        if 'artifact' in self.enabled_roles:
            artifact_source = self.config.get('artifact_source', {})
            source_type = artifact_source.get('type')
            summary['artifact'] = {
                'type': source_type,
            }
            
            if source_type == 'local':
                local_config = artifact_source.get('local', {})
                summary['artifact']['local'] = {
                    'domain': local_config.get('domain'),
                    'app_name': local_config.get('app_name'),
                }
            elif source_type == 'nexus':
                nexus_config = artifact_source.get('nexus', {})
                summary['artifact']['nexus'] = {
                    'url': nexus_config.get('url'),
                    'group_id': nexus_config.get('group_id'),
                    'artifact_id': nexus_config.get('artifact_id'),
                    'version': nexus_config.get('version'),
                }
        
        if 'cls' in self.enabled_roles:
            cls_java = self.config.get('neuron_cls_java', {})
            summary['cls'] = {
                'main_class': cls_java.get('main_class'),
                'java_home': cls_java.get('java_home'),
            }
        
        return summary


def main():
    """Main entry point for config parser."""
    if len(sys.argv) < 2:
        print("Usage: config_parser.py <inventory_file> [host]")
        sys.exit(1)
    
    inventory_file = sys.argv[1]
    host = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        with open(inventory_file, 'r') as f:
            inventory = yaml.safe_load(f)
        
        # Extract host variables
        if host:
            # Get specific host config
            all_hosts = inventory.get('all', {}).get('hosts', {})
            if host not in all_hosts:
                print(f"Error: Host '{host}' not found in inventory", file=sys.stderr)
                sys.exit(1)
            config = all_hosts[host]
        else:
            # Get first host config
            all_hosts = inventory.get('all', {}).get('hosts', {})
            if not all_hosts:
                print("Error: No hosts found in inventory", file=sys.stderr)
                sys.exit(1)
            config = list(all_hosts.values())[0]
        
        parser = ConfigParser(config)
        result = parser.parse()
        
        print(json.dumps(result, indent=2))
        
        if not result['validation']['valid']:
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

