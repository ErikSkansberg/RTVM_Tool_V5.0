# rtvm/utils/dependency_manager.py - Manages dependencies for the RTVM Tool

import sys
import subprocess
import importlib
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Define required packages with their corresponding import names
REQUIRED_PACKAGES: Dict[str, Optional[str]] = {
    "pandas": None,  # Import name is the same as package name
    "numpy": None,
    "matplotlib": None,
    "openpyxl": None,
    "pyspellchecker": "spellchecker",
    "reportlab": None,
    "pdfrw": None,
}

def check_dependency(package_name: str, import_name: Optional[str] = None) -> Tuple[bool, str]:
    """
    Checks if a dependency is installed and can be imported.
    
    Args:
        package_name: The name of the package to check
        import_name: The name used to import the package, if different from package_name
        
    Returns:
        Tuple of (is_installed, message)
    """
    import_name = import_name or package_name
    try:
        importlib.import_module(import_name)
        return True, f"Package '{package_name}' is already installed."
    except ImportError:
        return False, f"Package '{import_name}' is not installed."

def install_package(package_name: str) -> Tuple[bool, str]:
    """
    Attempts to install a package using pip.
    
    Args:
        package_name: The name of the package to install
        
    Returns:
        Tuple of (success, message)
    """
    try:
        logger.info(f"Installing package '{package_name}'...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name], 
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True, f"Successfully installed '{package_name}'."
    except subprocess.CalledProcessError as e:
        return False, f"Failed to install '{package_name}': {e}"
    except Exception as e:
        return False, f"Unexpected error installing '{package_name}': {e}"

def ensure_dependencies() -> None:
    """
    Ensures all required dependencies are installed.
    Attempts to install missing dependencies using pip.
    
    Raises:
        Exception: If a dependency fails to install
    """
    missing_packages = []
    
    # Check each dependency
    for package_name, import_name in REQUIRED_PACKAGES.items():
        is_installed, message = check_dependency(package_name, import_name)
        logger.debug(message)
        
        if not is_installed:
            missing_packages.append((package_name, import_name))
    
    # Install missing packages
    for package_name, import_name in missing_packages:
        success, message = install_package(package_name)
        logger.info(message)
        
        if not success:
            raise Exception(f"Failed to install {package_name}: {message}")
        
        # Verify the installation
        is_installed, _ = check_dependency(package_name, import_name)
        if not is_installed:
            raise Exception(f"Package {package_name} was installed but cannot be imported.")
