#!/usr/bin/env python3
"""
Integration tests for TWILIO_WHATSAPP_LINDY_SETUP.py

These tests verify that the setup script works correctly with the fixes:
- No async functions where not needed
- Proper import structure
- Correct function execution flow
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import inspect

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from TWILIO_WHATSAPP_LINDY_SETUP import TwilioWhatsAppLindySetup, main


class TestTwilioSetupStructure(unittest.TestCase):
    """Test the structure and setup of the TwilioWhatsAppLindySetup class"""
    
    def setUp(self):
        """Set up test environment variables"""
        self.env_vars = {
            'TWILIO_SID': 'AC_test_sid_12345',
            'TWILIO_AUTH_TOKEN': 'test_auth_token',
            'LINDY_API_KEY': 'test_lindy_key',
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_KEY': 'test_supabase_key',
            'WHATSAPP_PHONE': '+420123456789'
        }
        
        # Set environment variables
        for key, value in self.env_vars.items():
            os.environ[key] = value
    
    def tearDown(self):
        """Clean up environment variables"""
        for key in self.env_vars.keys():
            if key in os.environ:
                del os.environ[key]
    
    def test_no_async_functions(self):
        """Verify that step functions are NOT async (they shouldn't be)"""
        setup = TwilioWhatsAppLindySetup()
        
        # All step functions should be synchronous
        self.assertFalse(inspect.iscoroutinefunction(setup.step1_verify_twilio_connection))
        self.assertFalse(inspect.iscoroutinefunction(setup.step2_setup_lindy_integration))
        self.assertFalse(inspect.iscoroutinefunction(setup.step3_configure_webhooks))
        self.assertFalse(inspect.iscoroutinefunction(setup.step4_test_integration))
        self.assertFalse(inspect.iscoroutinefunction(setup.step5_enable_learning_mode))
    
    def test_main_is_not_async(self):
        """Verify that main() is synchronous"""
        self.assertFalse(inspect.iscoroutinefunction(main))
    
    def test_class_instantiation(self):
        """Test that class can be instantiated with env vars"""
        setup = TwilioWhatsAppLindySetup()
        
        # Verify credentials were loaded
        self.assertEqual(setup.credentials['TWILIO_SID'], 'AC_test_sid_12345')
        self.assertEqual(setup.credentials['TWILIO_AUTH_TOKEN'], 'test_auth_token')
        self.assertEqual(setup.credentials['LINDY_API_KEY'], 'test_lindy_key')
        self.assertEqual(setup.credentials['SUPABASE_URL'], 'https://test.supabase.co')
        self.assertEqual(setup.credentials['SUPABASE_KEY'], 'test_supabase_key')
        self.assertEqual(setup.credentials['WHATSAPP_PHONE'], '+420123456789')
    
    def test_base64_imported_at_module_level(self):
        """Verify base64 is available (imported at module level)"""
        import TWILIO_WHATSAPP_LINDY_SETUP as module
        
        # Check if base64 is in the module's namespace
        self.assertTrue(hasattr(module, 'base64'))
    
    @patch('TWILIO_WHATSAPP_LINDY_SETUP.requests.get')
    def test_step1_function_call(self, mock_get):
        """Test that step1 can be called synchronously"""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'friendly_name': 'Test Account',
            'sid': 'AC_test_sid_12345'
        }
        mock_get.return_value = mock_response
        
        setup = TwilioWhatsAppLindySetup()
        
        # Should be able to call directly (not await)
        result = setup.step1_verify_twilio_connection()
        
        # Verify it was called and returned a boolean
        self.assertIsInstance(result, bool)
        self.assertTrue(result)
    
    def test_all_steps_return_bool(self):
        """Verify all step functions have correct return type hints"""
        setup = TwilioWhatsAppLindySetup()
        
        # Get type hints
        step1_hints = inspect.signature(setup.step1_verify_twilio_connection).return_annotation
        step2_hints = inspect.signature(setup.step2_setup_lindy_integration).return_annotation
        step3_hints = inspect.signature(setup.step3_configure_webhooks).return_annotation
        step4_hints = inspect.signature(setup.step4_test_integration).return_annotation
        step5_hints = inspect.signature(setup.step5_enable_learning_mode).return_annotation
        
        # All should return bool
        self.assertEqual(step1_hints, bool)
        self.assertEqual(step2_hints, bool)
        self.assertEqual(step3_hints, bool)
        self.assertEqual(step4_hints, bool)
        self.assertEqual(step5_hints, bool)


class TestMainFunction(unittest.TestCase):
    """Test the main() function execution"""
    
    def setUp(self):
        """Set up test environment variables"""
        self.env_vars = {
            'TWILIO_SID': 'AC_test_sid_12345',
            'TWILIO_AUTH_TOKEN': 'test_auth_token',
            'LINDY_API_KEY': 'test_lindy_key',
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_KEY': 'test_supabase_key',
            'WHATSAPP_PHONE': '+420123456789'
        }
        
        for key, value in self.env_vars.items():
            os.environ[key] = value
    
    def tearDown(self):
        """Clean up environment variables"""
        for key in self.env_vars.keys():
            if key in os.environ:
                del os.environ[key]
    
    @patch('TWILIO_WHATSAPP_LINDY_SETUP.TwilioWhatsAppLindySetup.step5_enable_learning_mode')
    @patch('TWILIO_WHATSAPP_LINDY_SETUP.TwilioWhatsAppLindySetup.step4_test_integration')
    @patch('TWILIO_WHATSAPP_LINDY_SETUP.TwilioWhatsAppLindySetup.step3_configure_webhooks')
    @patch('TWILIO_WHATSAPP_LINDY_SETUP.TwilioWhatsAppLindySetup.step2_setup_lindy_integration')
    @patch('TWILIO_WHATSAPP_LINDY_SETUP.TwilioWhatsAppLindySetup.step1_verify_twilio_connection')
    def test_main_executes_all_steps(self, mock_step1, mock_step2, mock_step3, mock_step4, mock_step5):
        """Test that main() calls all steps in order"""
        # Mock all steps to return True
        mock_step1.return_value = True
        mock_step2.return_value = True
        mock_step3.return_value = True
        mock_step4.return_value = True
        mock_step5.return_value = True
        
        # Run main - should not raise any errors
        main()
        
        # Verify all steps were called
        mock_step1.assert_called_once()
        mock_step2.assert_called_once()
        mock_step3.assert_called_once()
        mock_step4.assert_called_once()
        mock_step5.assert_called_once()
    
    @patch('TWILIO_WHATSAPP_LINDY_SETUP.TwilioWhatsAppLindySetup.step1_verify_twilio_connection')
    def test_main_stops_on_failure(self, mock_step1):
        """Test that main() stops execution when a step fails"""
        # Mock step1 to return False (failure)
        mock_step1.return_value = False
        
        # Run main - should not raise errors, just stop
        main()
        
        # Verify step1 was called
        mock_step1.assert_called_once()


if __name__ == '__main__':
    unittest.main()
