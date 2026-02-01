"""
Tests for the secrets_loader module.

These tests verify that the secrets loader correctly:
1. Loads secrets from 1Password when available (mocked)
2. Falls back to .env files
3. Handles missing secrets appropriately
4. Handles errors gracefully (CLI not installed, not authenticated)
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from utils.secrets_loader import get_secret_from_1password, load_secret


class TestGet1PasswordSecret:
    """Test the get_secret_from_1password function"""
    
    def test_op_cli_not_found(self):
        """Test when op CLI is not installed"""
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            result = get_secret_from_1password(
                vault='AI',
                possible_item_names=['Test'],
                possible_field_names=['password']
            )
            assert result is None
    
    def test_op_cli_timeout(self):
        """Test when op CLI times out"""
        import subprocess
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('op', 10)):
            result = get_secret_from_1password(
                vault='AI',
                possible_item_names=['Test'],
                possible_field_names=['password']
            )
            assert result is None
    
    def test_op_cli_authentication_error(self):
        """Test when op CLI is not authenticated"""
        import subprocess
        mock_process = MagicMock()
        mock_process.stderr = "not signed in"
        with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'op', stderr="not signed in")):
            result = get_secret_from_1password(
                vault='AI',
                possible_item_names=['Test'],
                possible_field_names=['password']
            )
            assert result is None
    
    def test_successful_secret_retrieval(self):
        """Test successful secret retrieval from 1Password"""
        # Mock the two subprocess calls: list items, then get item
        list_response = MagicMock()
        list_response.stdout = '[{"id": "item123", "title": "Supabase"}]'
        
        get_response = MagicMock()
        get_response.stdout = '''{
            "id": "item123",
            "title": "Supabase",
            "fields": [
                {"label": "SUPABASE_KEY", "id": "password", "value": "test-secret-key"}
            ]
        }'''
        
        with patch('subprocess.run', side_effect=[list_response, get_response]):
            result = get_secret_from_1password(
                vault='AI',
                possible_item_names=['Supabase'],
                possible_field_names=['SUPABASE_KEY', 'key']
            )
            assert result == 'test-secret-key'
    
    def test_secret_not_found_in_vault(self):
        """Test when secret is not found in vault"""
        list_response = MagicMock()
        list_response.stdout = '[{"id": "item123", "title": "Other Item"}]'
        
        get_response = MagicMock()
        get_response.stdout = '''{
            "id": "item123",
            "title": "Other Item",
            "fields": [
                {"label": "different_field", "id": "text", "value": "some-value"}
            ]
        }'''
        
        with patch('subprocess.run', side_effect=[list_response, get_response]):
            result = get_secret_from_1password(
                vault='AI',
                possible_item_names=['Supabase'],
                possible_field_names=['SUPABASE_KEY']
            )
            assert result is None


class TestLoadSecret:
    """Test the load_secret function with fallback logic"""
    
    def test_load_from_1password_success(self):
        """Test loading secret from 1Password successfully"""
        with patch('utils.secrets_loader.get_secret_from_1password', return_value='1password-secret'):
            result = load_secret('TEST_KEY', vault='AI', required=True)
            assert result == '1password-secret'
    
    def test_fallback_to_env_file(self):
        """Test fallback to .env file when 1Password fails"""
        with patch('utils.secrets_loader.get_secret_from_1password', return_value=None):
            with patch.dict(os.environ, {'TEST_KEY': 'env-file-secret'}):
                result = load_secret('TEST_KEY', vault='AI', required=True)
                assert result == 'env-file-secret'
    
    def test_required_secret_missing_raises_error(self):
        """Test that missing required secret raises ValueError"""
        with patch('utils.secrets_loader.get_secret_from_1password', return_value=None):
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(ValueError) as exc_info:
                    load_secret('MISSING_KEY', vault='AI', required=True)
                
                assert 'MISSING_KEY' in str(exc_info.value)
                assert '1Password' in str(exc_info.value)
                assert '.env' in str(exc_info.value)
    
    def test_optional_secret_missing_returns_none(self):
        """Test that missing optional secret returns None"""
        with patch('utils.secrets_loader.get_secret_from_1password', return_value=None):
            with patch.dict(os.environ, {}, clear=True):
                result = load_secret('OPTIONAL_KEY', vault='AI', required=False)
                assert result is None
    
    def test_custom_item_and_field_names(self):
        """Test with custom item and field names"""
        with patch('utils.secrets_loader.get_secret_from_1password', return_value='custom-secret') as mock_get:
            result = load_secret(
                'API_KEY',
                vault='AI',
                item_names=['Custom Service', 'Backup Service'],
                field_names=['api_key', 'token', 'password'],
                required=True
            )
            assert result == 'custom-secret'
            # Verify the mock was called with correct parameters
            mock_get.assert_called_once_with(
                vault='AI',
                possible_item_names=['Custom Service', 'Backup Service'],
                possible_field_names=['api_key', 'token', 'password']
            )
    
    def test_default_field_names(self):
        """Test that default field names are used when not specified"""
        with patch('utils.secrets_loader.get_secret_from_1password', return_value='secret') as mock_get:
            load_secret('MY_KEY', vault='AI', required=True)
            
            # Check that default field names were used
            call_args = mock_get.call_args
            field_names = call_args.kwargs['possible_field_names']
            assert 'MY_KEY' in field_names
            assert 'password' in field_names
            assert 'secret' in field_names
            assert 'token' in field_names
            assert 'api_key' in field_names
            assert 'key' in field_names


class TestIntegration:
    """Integration tests for realistic scenarios"""
    
    def test_1password_priority_over_env(self):
        """Test that 1Password is checked before .env"""
        with patch('utils.secrets_loader.get_secret_from_1password', return_value='1password-value'):
            with patch.dict(os.environ, {'TEST_VAR': 'env-value'}):
                result = load_secret('TEST_VAR', vault='AI', required=True)
                # Should return 1Password value, not .env value
                assert result == '1password-value'
    
    def test_env_fallback_when_op_not_installed(self):
        """Test .env fallback when op CLI is not installed"""
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            with patch.dict(os.environ, {'FALLBACK_KEY': 'fallback-value'}):
                result = load_secret('FALLBACK_KEY', vault='AI', required=True)
                assert result == 'fallback-value'
