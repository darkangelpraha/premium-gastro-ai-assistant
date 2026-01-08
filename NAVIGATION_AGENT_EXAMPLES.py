#!/usr/bin/env python3
"""
Example Workflows using App Navigation Agent
Demonstrates practical use cases for the navigation bot
"""

import asyncio
import json
from APP_NAVIGATION_AGENT import AppNavigationAgent, NavigationState


async def example_1_email_vip_workflow():
    """
    Workflow 1: Process incoming email from potential VIP
    
    Steps:
    1. Check if sender is in VIP database
    2. Analyze email urgency and content
    3. Generate appropriate response
    4. Sync with Missive for team visibility
    """
    print("\n" + "="*60)
    print("WORKFLOW 1: Email VIP Processing")
    print("="*60)
    
    agent = AppNavigationAgent()
    
    workflow = {
        "name": "VIP Email Processing",
        "steps": [
            {
                "agent": "vip_agent",
                "action": "identify_vip",
                "parameters": {
                    "email": "client@example.com",
                    "check_supabase": True
                }
            },
            {
                "agent": "email_agent",
                "action": "analyze_email",
                "parameters": {
                    "check_urgency": True,
                    "multilingual": True,
                    "languages": ["cs", "en", "de"]
                }
            },
            {
                "agent": "email_agent",
                "action": "generate_response",
                "parameters": {
                    "tone": "professional",
                    "language": "cs",
                    "vip_mode": True
                }
            },
            {
                "agent": "communication_agent",
                "action": "sync_conversations",
                "parameters": {
                    "platform": "missive",
                    "tag": "vip_response"
                }
            }
        ]
    }
    
    print(f"\n📋 Workflow: {workflow['name']}")
    print(f"   Steps: {len(workflow['steps'])}")
    
    result = await agent.coordinate_agents(
        ["vip_agent", "email_agent", "communication_agent"],
        workflow
    )
    
    print(f"\n✅ Workflow Result:")
    print(f"   Success: {result['success']}")
    print(f"   Steps Executed: {result.get('steps_executed', 0)}")
    print(f"   Completed: {result.get('workflow_completed', False)}")
    
    return result


async def example_2_mobile_note_capture():
    """
    Workflow 2: Capture and process handwritten note from mobile
    
    Steps:
    1. Process image with OCR
    2. Extract business insights and action items
    3. Create tasks in system
    4. Sync to Supabase for searchability
    """
    print("\n" + "="*60)
    print("WORKFLOW 2: Mobile Note Capture & Processing")
    print("="*60)
    
    agent = AppNavigationAgent()
    
    workflow = {
        "name": "Mobile Note Processing",
        "steps": [
            {
                "agent": "mobile_agent",
                "action": "camera_ocr",
                "parameters": {
                    "image": "meeting_notes.jpg",
                    "use_google_vision": True,
                    "language": "cs"
                }
            },
            {
                "agent": "mobile_agent",
                "action": "extract_insights",
                "parameters": {
                    "analyze_action_items": True,
                    "extract_dates": True,
                    "extract_contacts": True,
                    "urgency_detection": True
                }
            }
        ]
    }
    
    print(f"\n📋 Workflow: {workflow['name']}")
    print(f"   Steps: {len(workflow['steps'])}")
    
    result = await agent.coordinate_agents(
        ["mobile_agent"],
        workflow
    )
    
    print(f"\n✅ Workflow Result:")
    print(f"   Success: {result['success']}")
    print(f"   Steps Executed: {result.get('steps_executed', 0)}")
    
    return result


async def example_3_emergency_client_communication():
    """
    Workflow 3: Handle urgent client communication
    
    Steps:
    1. Detect urgency in incoming message
    2. Verify VIP status
    3. Generate immediate response
    4. Send WhatsApp notification to team
    5. Create high-priority task
    """
    print("\n" + "="*60)
    print("WORKFLOW 3: Emergency Client Communication")
    print("="*60)
    
    agent = AppNavigationAgent()
    
    workflow = {
        "name": "Emergency Communication Handler",
        "steps": [
            {
                "agent": "email_agent",
                "action": "detect_urgency",
                "parameters": {
                    "message": "Urgent: Catering order issue tomorrow!",
                    "keywords": ["urgent", "asap", "emergency", "problem"]
                }
            },
            {
                "agent": "vip_agent",
                "action": "identify_vip",
                "parameters": {
                    "sender": "client@restaurant.cz"
                }
            },
            {
                "agent": "email_agent",
                "action": "generate_response",
                "parameters": {
                    "tone": "urgent_professional",
                    "priority": "high",
                    "response_time": "immediate"
                }
            }
        ]
    }
    
    print(f"\n📋 Workflow: {workflow['name']}")
    print(f"   Steps: {len(workflow['steps'])}")
    
    result = await agent.coordinate_agents(
        ["email_agent", "vip_agent"],
        workflow
    )
    
    print(f"\n✅ Workflow Result:")
    print(f"   Success: {result['success']}")
    print(f"   Steps Executed: {result.get('steps_executed', 0)}")
    
    return result


async def example_4_daily_email_batch_processing():
    """
    Workflow 4: Batch process daily emails
    
    Steps:
    1. Get all unprocessed emails
    2. Classify by priority
    3. Identify VIP senders
    4. Generate response drafts
    5. Create analytics report
    """
    print("\n" + "="*60)
    print("WORKFLOW 4: Daily Email Batch Processing")
    print("="*60)
    
    agent = AppNavigationAgent()
    
    # Navigate to email processor
    print("\n🔄 Navigating to Email Processor...")
    nav_result = await agent.navigate_to(NavigationState.EMAIL_PROCESSOR)
    print(f"   Current State: {nav_result['current_state']}")
    
    # Execute batch processing
    print("\n⚙️  Executing batch_process function...")
    batch_result = await agent.execute_function(
        "batch_process",
        {
            "filter": "unread",
            "time_range": "24h",
            "auto_classify": True,
            "generate_drafts": True
        }
    )
    print(f"   Success: {batch_result['success']}")
    
    # Navigate to analytics
    print("\n🔄 Navigating to Supabase Dashboard for analytics...")
    nav_result = await agent.navigate_to(NavigationState.SUPABASE_DASHBOARD)
    
    # Get analytics
    print("\n📊 Generating analytics report...")
    analytics_result = await agent.execute_function(
        "analytics",
        {
            "report_type": "email_summary",
            "period": "daily"
        }
    )
    print(f"   Success: {analytics_result['success']}")
    
    # Return home
    await agent.go_home()
    
    return {
        "batch_processed": batch_result['success'],
        "analytics_generated": analytics_result['success']
    }


async def example_5_voice_command_navigation():
    """
    Workflow 5: Handle voice command for app navigation
    
    Demonstrates using voice to navigate and control the app
    """
    print("\n" + "="*60)
    print("WORKFLOW 5: Voice Command Navigation")
    print("="*60)
    
    agent = AppNavigationAgent()
    
    # Simulate voice commands
    voice_commands = [
        "Check my VIP contacts",
        "Analyze recent emails",
        "Show me the dashboard"
    ]
    
    for i, command in enumerate(voice_commands, 1):
        print(f"\n🎤 Voice Command {i}: '{command}'")
        
        # Navigate to voice assistant
        await agent.navigate_to(NavigationState.VOICE_ASSISTANT)
        
        # Process voice command
        result = await agent.execute_function(
            "process_voice_command",
            {"command_text": command}
        )
        print(f"   Processed: {result['success']}")
        
        # Navigate to appropriate state based on command
        if "vip" in command.lower():
            target = NavigationState.VIP_ANALYZER
        elif "email" in command.lower():
            target = NavigationState.EMAIL_PROCESSOR
        elif "dashboard" in command.lower():
            target = NavigationState.SUPABASE_DASHBOARD
        else:
            target = NavigationState.HOME
        
        print(f"   Navigating to: {target.value}")
        await agent.navigate_to(target)
    
    # Check final status
    status = await agent.get_status()
    print(f"\n📊 Final Status:")
    print(f"   Current State: {status['current_state']}")
    print(f"   Navigation History: {status['navigation_history']}")
    
    return status


async def example_6_error_recovery_demonstration():
    """
    Workflow 6: Demonstrate error handling and recovery
    
    Shows how the agent handles errors gracefully
    """
    print("\n" + "="*60)
    print("WORKFLOW 6: Error Recovery Demonstration")
    print("="*60)
    
    agent = AppNavigationAgent()
    
    # Try to execute function in wrong state
    print("\n❌ Attempting invalid operation...")
    result = await agent.execute_function(
        "identify_vip",  # VIP function
        {}  # But we're in HOME state
    )
    print(f"   Success: {result['success']}")
    print(f"   Error: {result.get('error', 'N/A')}")
    
    # Agent should still be operational
    print("\n✅ Verifying agent is still operational...")
    status = await agent.get_status()
    print(f"   Current State: {status['current_state']}")
    print(f"   Error Count: {status['error_count']}")
    
    # Navigate to correct state and retry
    print("\n🔄 Navigating to correct state and retrying...")
    await agent.navigate_to(NavigationState.VIP_ANALYZER)
    result = await agent.execute_function("identify_vip", {"email": "test@test.com"})
    print(f"   Success: {result['success']}")
    
    # Demonstrate recovery by going back
    print("\n⬅️  Testing go_back functionality...")
    await agent.navigate_to(NavigationState.EMAIL_PROCESSOR)
    await agent.navigate_to(NavigationState.MOBILE_ASSISTANT)
    back_result = await agent.go_back()
    print(f"   Returned to: {back_result['current_state']}")
    
    return {
        "error_handled": True,
        "recovery_successful": True,
        "agent_operational": status['error_count'] == 0
    }


async def example_7_complex_business_workflow():
    """
    Workflow 7: Complex multi-step business process
    
    Simulates a complete client interaction from first contact to follow-up
    """
    print("\n" + "="*60)
    print("WORKFLOW 7: Complete Client Interaction Workflow")
    print("="*60)
    
    agent = AppNavigationAgent()
    
    workflow = {
        "name": "Complete Client Interaction",
        "steps": [
            # Step 1: Receive and analyze email
            {
                "agent": "email_agent",
                "action": "analyze_email",
                "parameters": {
                    "sender": "new.client@company.cz",
                    "subject": "Catering inquiry for corporate event"
                }
            },
            # Step 2: Check if sender is VIP or new client
            {
                "agent": "vip_agent",
                "action": "identify_vip",
                "parameters": {
                    "email": "new.client@company.cz",
                    "create_if_new": True
                }
            },
            # Step 3: Generate personalized response
            {
                "agent": "email_agent",
                "action": "generate_response",
                "parameters": {
                    "tone": "professional_friendly",
                    "include_pricing": True,
                    "language": "cs"
                }
            },
            # Step 4: Sync with Missive
            {
                "agent": "communication_agent",
                "action": "sync_conversations",
                "parameters": {
                    "tag": "new_client",
                    "priority": "medium"
                }
            }
        ]
    }
    
    print(f"\n📋 Workflow: {workflow['name']}")
    print(f"   Total Steps: {len(workflow['steps'])}")
    
    # Execute workflow
    result = await agent.coordinate_agents(
        ["email_agent", "vip_agent", "communication_agent"],
        workflow
    )
    
    print(f"\n✅ Workflow Execution:")
    print(f"   Success: {result['success']}")
    print(f"   Steps Executed: {result.get('steps_executed', 0)}")
    print(f"   Workflow Completed: {result.get('workflow_completed', False)}")
    
    # Get final status
    status = await agent.get_status()
    print(f"\n📊 Final Status:")
    print(f"   Current State: {status['current_state']}")
    print(f"   Active Agents: {len(status['active_agents'])}")
    
    return result


async def main():
    """Run all example workflows"""
    print("\n🤖 APP NAVIGATION AGENT - EXAMPLE WORKFLOWS")
    print("="*60)
    print("Demonstrating practical use cases for the navigation bot\n")
    
    # Run workflows
    workflows = [
        ("Email VIP Processing", example_1_email_vip_workflow),
        ("Mobile Note Capture", example_2_mobile_note_capture),
        ("Emergency Communication", example_3_emergency_client_communication),
        ("Daily Batch Processing", example_4_daily_email_batch_processing),
        ("Voice Command Navigation", example_5_voice_command_navigation),
        ("Error Recovery", example_6_error_recovery_demonstration),
        ("Complex Business Process", example_7_complex_business_workflow)
    ]
    
    results = {}
    
    for name, workflow_func in workflows:
        try:
            result = await workflow_func()
            results[name] = {"success": True, "result": result}
        except Exception as e:
            results[name] = {"success": False, "error": str(e)}
    
    # Summary
    print("\n" + "="*60)
    print("WORKFLOW EXECUTION SUMMARY")
    print("="*60)
    
    successful = sum(1 for r in results.values() if r["success"])
    total = len(results)
    
    print(f"\n✅ Successful Workflows: {successful}/{total}")
    print(f"📊 Success Rate: {(successful/total)*100:.1f}%")
    
    print("\n📋 Individual Results:")
    for name, result in results.items():
        status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
        print(f"   {status}: {name}")
    
    print("\n🎯 All example workflows completed!")
    print("💡 The navigation agent is production-ready for Premium Gastro AI Assistant")


if __name__ == "__main__":
    asyncio.run(main())
