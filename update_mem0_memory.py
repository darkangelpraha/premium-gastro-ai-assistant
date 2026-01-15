#!/usr/bin/env python3
"""
Update mem0 Memory System
Requires OPENAI_API_KEY environment variable
"""

import os
from mem0 import Memory

def main():
    print("=== mem0 Memory Update ===")

    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("✗ OPENAI_API_KEY environment variable not set")
        print("\nTo use mem0, set your OpenAI API key:")
        print("  export OPENAI_API_KEY='your-key-here'")
        print("\nOr add it to .env file:")
        print("  OPENAI_API_KEY=your-key-here")
        return False

    try:
        # Initialize mem0
        print("Initializing mem0...")
        memory = Memory()
        print("✓ mem0 initialized")

        # Critical rules to store
        rules = [
            {
                "content": "CRITICAL PROHIBITION: NEVER commit or push to git without explicit user approval. User stated: 'this behaviour is dangerous and therefore strictly prohibited!' on 2026-01-15. When user says 'nothing else', STOP and ASK before any git operations. Exception: Only when user explicitly says 'commit this' or 'push this' or 'create a PR'.",
                "metadata": {
                    "type": "behavioral_rule",
                    "severity": "critical",
                    "date": "2026-01-15",
                    "category": "git_operations"
                }
            },
            {
                "content": "CRITICAL BEHAVIORAL RULE: 'Who wants is looking for ways to do it, who does not want is looking for excuses.' User statement on 2026-01-15. Never make excuses. When faced with challenges: DON'T say 'I can't find it'. DO search harder using all methods. DO try multiple approaches. DO be resourceful and persistent. User called out: 'you are looking for excuses only, immediately start to look for solution and stop being lazy!'",
                "metadata": {
                    "type": "behavioral_rule",
                    "severity": "critical",
                    "date": "2026-01-15",
                    "category": "work_ethic"
                }
            },
            {
                "content": "Memory systems for Claude: 1. claude.md in project root, 2. mem0 API system (requires OpenAI key), 3. Quadrant (Qdrant) on NAS, 4. /root/.claude/MEMORY.md internal memory. All must be kept in sync with critical rules.",
                "metadata": {
                    "type": "system_info",
                    "severity": "medium",
                    "date": "2026-01-15",
                    "category": "memory_systems"
                }
            }
        ]

        # Add each rule to mem0
        print(f"\nAdding {len(rules)} rules to mem0...")
        for i, rule in enumerate(rules, 1):
            result = memory.add(
                rule["content"],
                user_id="claude_assistant",
                metadata=rule["metadata"]
            )
            print(f"  {i}. Added: {rule['metadata']['category']}")
            if result:
                print(f"     ID: {result}")

        print(f"\n✓ Successfully added {len(rules)} rules to mem0 memory")

        # Test retrieval
        print("\n=== Testing Memory Retrieval ===")
        test_query = "git commit push rules"
        print(f"Query: '{test_query}'")

        results = memory.search(test_query, user_id="claude_assistant", limit=2)
        if results:
            print(f"✓ Found {len(results)} relevant memories")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['memory'][:100]}...")
        else:
            print("No memories found (this might be expected if embeddings are still processing)")

        print(f"\n✓ mem0 memory update complete!")
        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print(f"\nTroubleshooting:")
        print(f"1. Verify OPENAI_API_KEY is correct")
        print(f"2. Check OpenAI API status")
        print(f"3. Ensure you have API credits available")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
