#!/usr/bin/env python3
"""
Tests for App Navigation Agent
"""

import pytest
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from APP_NAVIGATION_AGENT import (
    AppNavigationAgent,
    NavigationState,
    NavigationAction,
    NavigationContext,
    AgentCapability
)


class TestNavigationAgent:
    """Test suite for App Navigation Agent"""
    
    @pytest.fixture
    async def agent(self):
        """Create a fresh agent for each test"""
        return AppNavigationAgent()
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test agent initializes correctly"""
        agent = AppNavigationAgent()
        assert agent.context.current_state == NavigationState.HOME
        assert len(agent.app_structure) == 11  # All navigation states
        assert len(agent.agent_registry) == 4  # All registered agents
        assert agent.context.error_count == 0
    
    @pytest.mark.asyncio
    async def test_basic_navigation(self):
        """Test basic navigation between states"""
        agent = AppNavigationAgent()
        
        # Navigate to email processor
        result = await agent.navigate_to(NavigationState.EMAIL_PROCESSOR)
        assert result['success'] is True
        assert result['current_state'] == NavigationState.EMAIL_PROCESSOR.value
        assert agent.context.current_state == NavigationState.EMAIL_PROCESSOR
    
    @pytest.mark.asyncio
    async def test_navigation_history(self):
        """Test navigation history is maintained"""
        agent = AppNavigationAgent()
        
        # Navigate through multiple states
        await agent.navigate_to(NavigationState.EMAIL_PROCESSOR)
        await agent.navigate_to(NavigationState.VIP_ANALYZER)
        await agent.navigate_to(NavigationState.MOBILE_ASSISTANT)
        
        # Check history
        assert len(agent.context.previous_states) == 3
        assert agent.context.previous_states[0] == NavigationState.HOME
        assert agent.context.previous_states[1] == NavigationState.EMAIL_PROCESSOR
        assert agent.context.previous_states[2] == NavigationState.VIP_ANALYZER
    
    @pytest.mark.asyncio
    async def test_go_back(self):
        """Test going back to previous state"""
        agent = AppNavigationAgent()
        
        # Navigate forward
        await agent.navigate_to(NavigationState.EMAIL_PROCESSOR)
        await agent.navigate_to(NavigationState.VIP_ANALYZER)
        
        # Go back
        result = await agent.go_back()
        assert result['success'] is True
        assert agent.context.current_state == NavigationState.EMAIL_PROCESSOR
    
    @pytest.mark.asyncio
    async def test_go_home(self):
        """Test returning to home state"""
        agent = AppNavigationAgent()
        
        # Navigate to different state
        await agent.navigate_to(NavigationState.EMAIL_PROCESSOR)
        
        # Go home
        result = await agent.go_home()
        assert result['success'] is True
        assert agent.context.current_state == NavigationState.HOME
    
    @pytest.mark.asyncio
    async def test_execute_function(self):
        """Test executing functions in current state"""
        agent = AppNavigationAgent()
        
        # Navigate to email processor
        await agent.navigate_to(NavigationState.EMAIL_PROCESSOR)
        
        # Execute function
        result = await agent.execute_function("analyze_email", {"email_id": "123"})
        assert result['success'] is True
        assert result['function'] == "analyze_email"
        assert result['state'] == NavigationState.EMAIL_PROCESSOR.value
    
    @pytest.mark.asyncio
    async def test_execute_invalid_function(self):
        """Test executing function not available in current state"""
        agent = AppNavigationAgent()
        
        # Try to execute VIP function while in HOME state
        result = await agent.execute_function("identify_vip", {})
        assert result['success'] is False
        assert 'not available' in result['error']
    
    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test getting current status"""
        agent = AppNavigationAgent()
        
        await agent.navigate_to(NavigationState.EMAIL_PROCESSOR)
        
        status = await agent.get_status()
        assert status['current_state'] == NavigationState.EMAIL_PROCESSOR.value
        assert 'available_functions' in status
        assert 'navigation_history' in status
        assert status['error_count'] == 0
    
    @pytest.mark.asyncio
    async def test_list_available_states(self):
        """Test listing all available states"""
        agent = AppNavigationAgent()
        
        states = await agent.list_available_states()
        assert states['total_states'] == 11
        assert len(states['states']) == 11
        assert states['current_state'] == NavigationState.HOME.value
    
    @pytest.mark.asyncio
    async def test_navigation_with_parameters(self):
        """Test navigation with parameters"""
        agent = AppNavigationAgent()
        
        params = {"test_param": "value", "another": 123}
        result = await agent.navigate_to(NavigationState.EMAIL_PROCESSOR, params)
        
        assert result['success'] is True
        assert agent.context.parameters['test_param'] == "value"
        assert agent.context.parameters['another'] == 123
    
    @pytest.mark.asyncio
    async def test_multi_agent_coordination(self):
        """Test coordinating multiple agents"""
        agent = AppNavigationAgent()
        
        workflow = {
            "steps": [
                {
                    "agent": "vip_agent",
                    "action": "identify_vip",
                    "parameters": {"email": "test@example.com"}
                },
                {
                    "agent": "email_agent",
                    "action": "analyze_email",
                    "parameters": {"priority": "high"}
                }
            ]
        }
        
        result = await agent.coordinate_agents(
            ["vip_agent", "email_agent"],
            workflow
        )
        
        assert result['success'] is True
        assert result['workflow_completed'] is True
        assert result['steps_executed'] == 2
        assert len(result['results']) == 2
    
    @pytest.mark.asyncio
    async def test_coordinate_invalid_agent(self):
        """Test coordinating with non-existent agent"""
        agent = AppNavigationAgent()
        
        workflow = {"steps": []}
        result = await agent.coordinate_agents(
            ["nonexistent_agent"],
            workflow
        )
        
        assert result['success'] is False
        assert 'not found' in result['error']
    
    @pytest.mark.asyncio
    async def test_navigation_validation(self):
        """Test navigation validation rules"""
        agent = AppNavigationAgent()
        
        # Test valid navigation from HOME
        validation = agent._validate_navigation(NavigationState.EMAIL_PROCESSOR)
        assert validation['valid'] is True
    
    @pytest.mark.asyncio
    async def test_dependency_checking(self):
        """Test dependency checking"""
        agent = AppNavigationAgent()
        
        # Check dependencies for email processor
        deps = agent._check_dependencies(NavigationState.EMAIL_PROCESSOR)
        assert deps['satisfied'] is True
        assert isinstance(deps['dependencies'], list)
    
    @pytest.mark.asyncio
    async def test_error_classification(self):
        """Test error type classification"""
        agent = AppNavigationAgent()
        
        # Test different error types
        not_found_error = Exception("Module not found")
        assert agent._classify_error(not_found_error) == "module_not_found"
        
        permission_error = Exception("Permission denied")
        assert agent._classify_error(permission_error) == "permission_denied"
        
        timeout_error = Exception("Operation timeout")
        assert agent._classify_error(timeout_error) == "timeout"
        
        general_error = Exception("Something went wrong")
        assert agent._classify_error(general_error) == "general_error"
    
    @pytest.mark.asyncio
    async def test_error_recovery_navigation(self):
        """Test error recovery for navigation errors"""
        agent = AppNavigationAgent()
        
        # Navigate to a state first
        await agent.navigate_to(NavigationState.EMAIL_PROCESSOR)
        
        # Simulate error recovery
        error = Exception("Navigation failed")
        recovery = await agent._recover_from_navigation_error(
            error, 
            NavigationState.VIP_ANALYZER
        )
        
        assert recovery['recovered'] is True
        assert 'action' in recovery
    
    @pytest.mark.asyncio
    async def test_state_persistence(self):
        """Test that state is properly maintained"""
        agent = AppNavigationAgent()
        
        # Navigate through several states
        await agent.navigate_to(NavigationState.EMAIL_PROCESSOR)
        await agent.navigate_to(NavigationState.VIP_ANALYZER)
        
        # Check state is correct
        assert agent.context.current_state == NavigationState.VIP_ANALYZER
        
        # Go back
        await agent.go_back()
        assert agent.context.current_state == NavigationState.EMAIL_PROCESSOR
    
    @pytest.mark.asyncio
    async def test_app_structure_integrity(self):
        """Test that app structure is properly defined"""
        agent = AppNavigationAgent()
        
        # Check all states have required attributes
        for state, capability in agent.app_structure.items():
            assert isinstance(capability, AgentCapability)
            assert capability.name is not None
            assert capability.state == state
            assert isinstance(capability.available_functions, list)
            assert isinstance(capability.required_permissions, list)
            assert isinstance(capability.dependencies, list)
    
    @pytest.mark.asyncio
    async def test_agent_registry_integrity(self):
        """Test that agent registry is properly defined"""
        agent = AppNavigationAgent()
        
        # Check all agents have required attributes
        for agent_name, agent_info in agent.agent_registry.items():
            assert 'module' in agent_info
            assert 'state' in agent_info
            assert 'status' in agent_info
            assert 'capabilities' in agent_info
            assert isinstance(agent_info['state'], NavigationState)
    
    @pytest.mark.asyncio
    async def test_sequential_navigation(self):
        """Test multiple sequential navigations"""
        agent = AppNavigationAgent()
        
        states = [
            NavigationState.EMAIL_PROCESSOR,
            NavigationState.VIP_ANALYZER,
            NavigationState.MOBILE_ASSISTANT,
            NavigationState.MISSIVE_INTEGRATION
        ]
        
        for state in states:
            result = await agent.navigate_to(state)
            assert result['success'] is True
            assert agent.context.current_state == state
    
    @pytest.mark.asyncio
    async def test_navigation_context_reset(self):
        """Test that context error count resets on successful navigation"""
        agent = AppNavigationAgent()
        
        # Simulate some errors
        agent.context.error_count = 5
        
        # Navigate successfully
        await agent.navigate_to(NavigationState.EMAIL_PROCESSOR)
        
        # Error count should reset
        assert agent.context.error_count == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_safe_operations(self):
        """Test that agent handles operations safely"""
        agent = AppNavigationAgent()
        
        # Execute multiple operations
        results = await asyncio.gather(
            agent.navigate_to(NavigationState.EMAIL_PROCESSOR),
            agent.get_status(),
            agent.list_available_states()
        )
        
        # All should complete successfully
        assert all(r is not None for r in results)
    
    @pytest.mark.asyncio
    async def test_workflow_with_multiple_steps(self):
        """Test complex workflow with multiple steps"""
        agent = AppNavigationAgent()
        
        workflow = {
            "steps": [
                {
                    "agent": "vip_agent",
                    "action": "identify_vip",
                    "parameters": {"contact": "client1"}
                },
                {
                    "agent": "email_agent",
                    "action": "analyze_email",
                    "parameters": {"email_id": "456"}
                },
                {
                    "agent": "communication_agent",
                    "action": "sync_conversations",
                    "parameters": {"sync": True}
                }
            ]
        }
        
        result = await agent.coordinate_agents(
            ["vip_agent", "email_agent", "communication_agent"],
            workflow
        )
        
        assert result['success'] is True
        assert result['steps_executed'] == 3


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
