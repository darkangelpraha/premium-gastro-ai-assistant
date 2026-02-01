#!/usr/bin/env python3
"""
Secure secrets loader - loads credentials from 1Password (op) with .env fallback
"""

import os
import subprocess
import json
import logging
from typing import Optional, List
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def get_secret_from_1password(
    vault: str = "AI",
    possible_item_names: Optional[List[str]] = None,
    possible_field_names: Optional[List[str]] = None
) -> Optional[str]:
    """
    Retrieve a secret from 1Password vault.
    
    Args:
        vault: Name of the 1Password vault (default: "AI")
        possible_item_names: List of possible item titles to search
        possible_field_names: List of possible field labels/names to search
    
    Returns:
        The secret value if found, None otherwise
    """
    try:
        # List all items in the vault
        result = subprocess.run(
            ['op', 'item', 'list', '--vault', vault, '--format', 'json'],
            capture_output=True,
            check=True,
            text=True,
            timeout=10
        )
        items = json.loads(result.stdout)
        
        for item in items:
            # Check if item name matches (if specified)
            if possible_item_names:
                item_title = item.get('title', '').lower()
                if not any(name.lower() in item_title for name in possible_item_names):
                    continue
            
            item_id = item.get("id")
            if not item_id:
                continue
                
            # Fetch the full item details
            item_json = subprocess.run(
                ['op', 'item', 'get', item_id, '--vault', vault, '--format', 'json'],
                capture_output=True,
                check=True,
                text=True,
                timeout=10
            )
            full_item = json.loads(item_json.stdout)
            
            # Search through fields
            fields = full_item.get('fields', [])
            for field in fields:
                field_label = field.get('label', '').lower()
                field_id = field.get('id', '').lower()
                value = field.get('value')
                
                if not value:
                    continue
                
                # Check if field name matches
                if possible_field_names:
                    for fname in possible_field_names:
                        if fname.lower() in field_label or fname.lower() in field_id:
                            logger.info(
                                f"Loaded secret from 1Password: vault='{vault}', "
                                f"item='{full_item.get('title')}', field='{field_label}'"
                            )
                            return value
                else:
                    # If no field names specified, return first value found
                    logger.info(
                        f"Loaded secret from 1Password: vault='{vault}', "
                        f"item='{full_item.get('title')}', field='{field_label}'"
                    )
                    return value
                    
        logger.warning(
            f"Secret not found in 1Password vault '{vault}' "
            f"(items: {possible_item_names}, fields: {possible_field_names})"
        )
                    
    except subprocess.TimeoutExpired:
        logger.error("1Password CLI timeout - is op CLI installed and authenticated?")
    except subprocess.CalledProcessError as e:
        logger.error(f"1Password CLI error: {e.stderr if e.stderr else str(e)}")
    except FileNotFoundError:
        logger.warning("1Password CLI (op) not found - install from https://1password.com/downloads/command-line/")
    except Exception as e:
        logger.error(f"Error retrieving secret from 1Password: {e}")
    
    return None


def load_secret(
    env_var_name: str,
    vault: str = "AI",
    item_names: Optional[List[str]] = None,
    field_names: Optional[List[str]] = None,
    required: bool = True
) -> Optional[str]:
    """
    Load a secret from 1Password, with fallback to .env file.
    
    Args:
        env_var_name: Environment variable name (used for .env fallback)
        vault: 1Password vault name
        item_names: Possible 1Password item names to search
        field_names: Possible field names in 1Password items
        required: If True, raises ValueError when secret not found
    
    Returns:
        The secret value
        
    Raises:
        ValueError: If required=True and secret not found
    """
    # Try 1Password first
    secret = get_secret_from_1password(
        vault=vault,
        possible_item_names=item_names or [env_var_name],
        possible_field_names=field_names or [
            env_var_name,
            'password',
            'secret',
            'token',
            'api_key',
            'key'
        ]
    )
    
    if secret:
        return secret
    
    # Fall back to .env
    load_dotenv()
    secret = os.getenv(env_var_name)
    
    if secret:
        logger.info(f"Loaded {env_var_name} from .env file")
        return secret
    
    # Not found anywhere
    if required:
        raise ValueError(
            f"{env_var_name} not found in 1Password vault '{vault}' or .env file. "
            f"Please configure this credential in 1Password or add to .env file."
        )
    
    logger.warning(f"{env_var_name} not found (optional)")
    return None
