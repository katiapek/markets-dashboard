from typing import Any, Optional, Union
from datetime import datetime
import re
import logging
from app.error_logging import log_error
from exceptions import InputValidationError, InputFormatError, InputRangeError

class InputHandler:
    """Centralized input handling with validation, sanitization, and error management"""
    
    def __init__(self):
        self._input_state = {}
        self._validation_rules = {}
        self._error_messages = {}
        self._logger = logging.getLogger('input_handler')
        
    def register_input(self, input_name: str, validation_rules: dict, error_messages: Optional[dict] = None):
        """Register an input with its validation rules and error messages"""
        self._validation_rules[input_name] = validation_rules
        self._error_messages[input_name] = error_messages or {}
        self._input_state[input_name] = {
            'value': None,
            'is_valid': False,
            'errors': []
        }
        
    def validate_input(self, input_name: str, value: Any) -> bool:
        """Validate input against registered rules"""
        if input_name not in self._validation_rules:
            raise ValueError(f"Input '{input_name}' not registered")
            
        self._input_state[input_name]['value'] = value
        self._input_state[input_name]['errors'] = []
        
        rules = self._validation_rules[input_name]
        errors = []
        
        # Type validation
        if 'type' in rules and not isinstance(value, rules['type']):
            errors.append(self._get_error_message(input_name, 'type'))
            
        # Required validation
        if rules.get('required', False) and value in (None, '', []):
            errors.append(self._get_error_message(input_name, 'required'))
            
        # Range validation
        if 'min' in rules and value < rules['min']:
            errors.append(self._get_error_message(input_name, 'min'))
        if 'max' in rules and value > rules['max']:
            errors.append(self._get_error_message(input_name, 'max'))
            
        # Pattern validation
        if 'pattern' in rules and isinstance(value, str):
            if not re.match(rules['pattern'], value):
                errors.append(self._get_error_message(input_name, 'pattern'))
                
        # Custom validation
        if 'custom' in rules:
            custom_result = rules['custom'](value)
            if isinstance(custom_result, str):
                errors.append(custom_result)
                
        self._input_state[input_name]['errors'] = errors
        self._input_state[input_name]['is_valid'] = not bool(errors)
        
        if errors:
            log_error({
                'input_name': input_name,
                'value': value,
                'errors': errors,
                'timestamp': datetime.now().isoformat()
            })
            return False
            
        return True
        
    def get_input_state(self, input_name: str) -> dict:
        """Get current state of an input"""
        return self._input_state.get(input_name, {})
        
    def get_input_value(self, input_name: str) -> Any:
        """Get current value of an input"""
        return self._input_state.get(input_name, {}).get('value')
        
    def get_input_errors(self, input_name: str) -> list:
        """Get current errors for an input"""
        return self._input_state.get(input_name, {}).get('errors', [])
        
    def is_input_valid(self, input_name: str) -> bool:
        """Check if an input is valid"""
        return self._input_state.get(input_name, {}).get('is_valid', False)
        
    def _get_error_message(self, input_name: str, error_type: str) -> str:
        """Get formatted error message"""
        default_messages = {
            'type': f"Invalid type for {input_name}",
            'required': f"{input_name} is required",
            'min': f"{input_name} is below minimum value",
            'max': f"{input_name} is above maximum value",
            'pattern': f"{input_name} has invalid format"
        }
        return self._error_messages[input_name].get(error_type, default_messages.get(error_type, "Invalid input"))
        
    def sanitize_input(self, input_name: str, value: Any) -> Any:
        """Sanitize input value"""
        if input_name not in self._validation_rules:
            raise ValueError(f"Input '{input_name}' not registered")
            
        rules = self._validation_rules[input_name]
        
        # String sanitization
        if isinstance(value, str):
            value = value.strip()
            if rules.get('trim', True):
                value = value.strip()
            if rules.get('lowercase', False):
                value = value.lower()
            if rules.get('uppercase', False):
                value = value.upper()
                
        # Numeric sanitization
        if isinstance(value, (int, float)):
            if 'round' in rules:
                value = round(value, rules['round'])
                
        return value
        
    def reset_input(self, input_name: str):
        """Reset input state"""
        if input_name in self._input_state:
            self._input_state[input_name] = {
                'value': None,
                'is_valid': False,
                'errors': []
            }
