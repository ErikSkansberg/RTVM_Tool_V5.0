# rtvm/utils/config.py - Configuration management for the RTVM Tool

import os
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    "ui": {
        "theme": "default",
        "font_size": 10,
        "show_history_tables": False,
        "show_progress_bar": False,
        "window_width": 1600,
        "window_height": 800
    },
    "paths": {
        "last_excel_file": "",
        "last_output_directory": "",
        "disagreement_reports_folder": "",
        "template_file_path": ""
    },
    "reports": {
        "company_name": "Birdon",
        "contract_number": "70Z02323D93270001",
        "distribution_statement": "DISTRIBUTION STATEMENT D: DISTRIBUTION AUTHORIZED TO DHS/CG/DOD AND THEIR CONTRACTORS ONLY DUE TO ADMINISTRATIVE OR OPERATIONAL USE (5 OCT 2022). OTHER REQUESTS SHALL BE REFERRED TO COMMANDANT (CG-9327).",
        "destruction_notice": "DESTRUCTION NOTICE: DESTROY THIS DOCUMENT BY ANY METHOD THAT WILL PREVENT DISCLOSURE OF CONTENTS OR RECONSTRUCTION OF THE DOCUMENT.",
    },
    "vessel_types": [
        "160-WLIC",
        "180-WLR"
    ],
    "swbs_groups": {
        "SWBS 000": [
            "040-001", "042-001", "042-003", "042-005", "045-001",
            "068-001", "068-002", "068-003", "070-001", "073-001",
            "073-003", "073-006", "073-007", "073-008", "073-009",
            "076-002", "077-001", "077-002", "083-002", "085-004",
            "086-003", "088-001", "088-002", "088-005", "088-007",
            "092-001", "096-004"
        ],
        "SWBS 100": [
            "100-001", "100-002", "100-004", "100-006", "100-010",
            "100-011", "100-012", "100-013"
        ],
        "SWBS 200": [
            "200-001", "200-003", "233-001", "245-001", "245-002",
            "245-003", "249-001", "249-002", "249-003", "249-004",
            "259-001"
        ],
        "SWBS 202": [
            "202-012"
        ],
        "SWBS 300": [
            "300-001", "300-002", "300-003", "300-006", "300-007",
            "300-008", "300-009", "300-010", "300-011", "302-001",
            "310-001", "320-003", "303-001"
        ],
        "SWBS 400": [
            "400-001", "400-002", "400-003", "400-010", "400-011",
            "402-001", "402-002", "405-001", "407-001", "428-001",
            "432-001", "432-002", "435-001", "436-002", "440-001"
        ],
        "SWBS 500": [
            "508-001", "555-001", "580-001", "580-004", "583-001",
            "589-002", "593-002", "593-005", "521-003"
        ],
        "SWBS 600": [
            "602-001", "604-001", "634-001", "640-002"
        ]
    }
}

class Config:
    """
    Configuration manager for the RTVM Tool.
    Handles loading, saving, and accessing configuration values.
    """
    
    def __init__(self):
        """Initialize the Config object with default settings."""
        self.config_dir = os.path.join(os.path.expanduser("~"), ".rtvm_tool")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.settings = dict(DEFAULT_CONFIG)  # Create a copy of the default config
        self._ensure_config_dir()
        self.load()
    
    def _ensure_config_dir(self) -> None:
        """Create the configuration directory if it doesn't exist."""
        os.makedirs(self.config_dir, exist_ok=True)
    
    def load(self) -> None:
        """Load configuration from file or create default if not exists."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                # Update the default config with saved values
                self._deep_update(self.settings, saved_config)
                logger.info("Configuration loaded from file")
            else:
                self.save()  # Save default config
                logger.info("Created default configuration file")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            # Keep using the default config
    
    def save(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            logger.info("Configuration saved to file")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            section: The configuration section
            key: The configuration key
            default: Default value if not found
            
        Returns:
            The configuration value or default if not found
        """
        try:
            return self.settings[section][key]
        except KeyError:
            return default
    
    def set(self, section: str, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            section: The configuration section
            key: The configuration key
            value: The value to set
        """
        # Create section if it doesn't exist
        if section not in self.settings:
            self.settings[section] = {}
        
        self.settings[section][key] = value
        self.save()
    
    def _deep_update(self, target: Dict, source: Dict) -> None:
        """
        Recursively update a nested dictionary with values from another.
        
        Args:
            target: The dictionary to update
            source: The dictionary to get values from
        """
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value

# Singleton instance
config = Config()
