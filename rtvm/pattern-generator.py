# rtvm/models/pattern_generator.py - Pattern generation functionality

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class PatternGenerator:
    """
    Handles the generation of verification patterns for RTVM entries.
    """
    
    @staticmethod
    def generate_standard_pattern(
        obj_identifier: str,
        cdrl_name: str,
        page_sheet_type: str,
        page_sheet: str,
        plan_view_type: str,
        plan_view: str,
        status: str
    ) -> str:
        """
        Generate a standard verification pattern.
        
        Args:
            obj_identifier: The object identifier (e.g. WCC-VERI-DOC-1234)
            cdrl_name: The CDRL file name
            page_sheet_type: Either "Page" or "Sheet"
            page_sheet: The page or sheet number
            plan_view_type: Either "Plan View" or "Section"
            plan_view: The plan view or section identifier
            status: The status (e.g. "SAT" or "UNSAT")
            
        Returns:
            The generated pattern string
        """
        # Normalize inputs
        obj_identifier = obj_identifier.upper() if obj_identifier else ""
        cdrl_name = cdrl_name.upper() if cdrl_name else ""
        page_sheet = str(page_sheet) if page_sheet else ""
        plan_view = str(plan_view) if plan_view else ""
        status = status.upper() if status else ""
        
        # Construct detailed location string
        detailed_location = f"{cdrl_name}, {page_sheet_type} {page_sheet}, {plan_view_type} {plan_view}"
        
        # Generate the pattern
        pattern = f"{obj_identifier};{detailed_location};{status}"
        
        logger.debug(f"Generated standard pattern: {pattern}")
        return pattern
    
    @staticmethod
    def generate_vessel_specific_pattern(
        vessel_type: str,
        di_number: str,
        cdrl_name: str,
        page_sheet_type: str,
        page_sheet: str,
        plan_view_type: str,
        plan_view: str,
        status: str
    ) -> str:
        """
        Generate a vessel-specific verification pattern.
        
        Args:
            vessel_type: The vessel type (e.g. "160-WLIC" or "180-WLR")
            di_number: The DI number
            cdrl_name: The CDRL file name
            page_sheet_type: Either "Page" or "Sheet"
            page_sheet: The page or sheet number
            plan_view_type: Either "Plan View" or "Section"
            plan_view: The plan view or section identifier
            status: The status (e.g. "SAT" or "UNSAT")
            
        Returns:
            The generated pattern string
        """
        # Normalize inputs
        vessel_type = vessel_type.upper() if vessel_type else ""
        di_number = di_number.upper() if di_number else ""
        cdrl_name = cdrl_name.upper() if cdrl_name else ""
        page_sheet = str(page_sheet) if page_sheet else ""
        plan_view = str(plan_view) if plan_view else ""
        status = status.upper() if status else ""
        
        # Construct detailed location string
        detailed_location = f"{cdrl_name}, {page_sheet_type} {page_sheet}, {plan_view_type} {plan_view}"
        
        # For 180-WLR, replace any reference to 160-WLIC in the detailed location
        if vessel_type == "180-WLR":
            detailed_location = detailed_location.replace("160-WLIC", "180-WLR")
        
        # Generate the pattern with ADD prefix
        pattern = f"ADD;{di_number};{detailed_location};{status}"
        
        logger.debug(f"Generated vessel-specific pattern for {vessel_type}: {pattern}")
        return pattern
    
    @staticmethod
    def generate_deletion_pattern(obj_identifier: str) -> str:
        """
        Generate a deletion pattern for the specified object identifier.
        
        Args:
            obj_identifier: The object identifier (e.g. WCC-VERI-DOC-1234)
            
        Returns:
            The deletion pattern string
        """
        # Normalize input
        obj_identifier = obj_identifier.upper() if obj_identifier else ""
        
        # Generate the pattern
        pattern = f"DEL; {obj_identifier}"
        
        logger.debug(f"Generated deletion pattern: {pattern}")
        return pattern
    
    @staticmethod
    def validate_pattern_inputs(
        obj_identifier: str,
        cdrl_name: str,
        page_sheet: str,
        plan_view: str,
        status: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate inputs for pattern generation.
        
        Args:
            obj_identifier: The object identifier
            cdrl_name: The CDRL file name
            page_sheet: The page or sheet number
            plan_view: The plan view or section identifier
            status: The status
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        is_valid = True
        error_messages = []
        
        if not obj_identifier:
            error_messages.append("Object Identifier is required.")
            is_valid = False
        
        if not cdrl_name:
            error_messages.append("CDRL File Name is required.")
            is_valid = False
        
        if not page_sheet:
            error_messages.append("Page/Sheet input is required.")
            is_valid = False
        
        if not plan_view:
            error_messages.append("Plan View/Section input is required.")
            is_valid = False
        
        if not status:
            error_messages.append("Contractor Assessed Status is required.")
            is_valid = False
        
        return is_valid, error_messages
