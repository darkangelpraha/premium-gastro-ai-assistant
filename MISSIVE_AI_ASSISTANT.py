#!/usr/bin/env python3
"""
MISSIVE AI ASSISTANT - CONTEXT-AWARE EMAIL INTELLIGENCE
Reads Gmail via Missive API, understands relationships, drafts intelligent responses
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

@dataclass
class EmailContext:
    thread_id: str
    sender: str
    subject: str
    content: str
    timestamp: str
    participants: List[str]
    related_threads: List[str] = None
    urgency_score: int = 5
    requires_response: bool = True
    draft_response: str = ""

class MissiveAIAssistant:
    """Context-aware email assistant using Missive API"""
    
    def __init__(self):
        # Missive API credentials (get from 1Password)
        self.missive_token = os.getenv('MISSIVE_API_TOKEN')
        self.missive_org = os.getenv('MISSIVE_ORG_ID')
        
        # Missive API base
        self.api_base = "https://public-api.missiveapp.com/v1"
        
        # Headers for Missive API
        self.headers = {
            'Authorization': f'Bearer {self.missive_token}',
            'Content-Type': 'application/json'
        }
        
        # Supabase intelligence database (40,803+ records)
        self.supabase_url = "https://lowgijppjapmetedkvjb.supabase.co"
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.supabase_headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json'
        }
        
        # Context database - tracks relationships
        self.conversation_context = {}
        self.client_supplier_map = {}
        self.contact_intelligence = {}  # Cache for contact data
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_unread_emails(self, hours_back: int = 24) -> List[EmailContext]:
        """Get unread emails from last N hours with full context"""
        try:
            # Get conversations from Missive
            conversations_url = f"{self.api_base}/conversations"
            params = {
                'limit': 50,
                'filter': 'unread',
                'include': 'messages,participants'
            }
            
            response = requests.get(conversations_url, headers=self.headers, params=params)
            response.raise_for_status()
            
            conversations_data = response.json()
            email_contexts = []
            
            for conv in conversations_data.get('conversations', []):
                context = self._build_email_context(conv)
                if context:
                    email_contexts.append(context)
            
            # Analyze relationships between emails
            self._analyze_relationships(email_contexts)
            
            # Sort by urgency
            email_contexts.sort(key=lambda x: x.urgency_score, reverse=True)
            
            return email_contexts
            
        except Exception as e:
            self.logger.error(f"Error fetching emails: {e}")
            return []
    
    def _build_email_context(self, conversation: Dict) -> Optional[EmailContext]:
        """Build rich context from conversation data"""
        try:
            messages = conversation.get('messages', [])
            if not messages:
                return None
            
            # Get latest message
            latest_message = messages[-1]
            
            # Extract participants
            participants = []
            for participant in conversation.get('participants', []):
                email = participant.get('email', '')
                if email:
                    participants.append(email)
            
            # Build context
            context = EmailContext(
                thread_id=conversation['id'],
                sender=latest_message.get('from_field', {}).get('address', ''),
                subject=conversation.get('subject', ''),
                content=latest_message.get('body', ''),
                timestamp=latest_message.get('created_at', ''),
                participants=participants
            )
            
            # Calculate urgency
            context.urgency_score = self._calculate_urgency(context)
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error building context: {e}")
            return None
    
    def _calculate_urgency(self, context: EmailContext) -> int:
        """Calculate email urgency score 1-10"""
        score = 5
        
        # Content urgency keywords
        urgent_words = ['urgent', 'asap', 'emergency', 'critical', 'immediately', 'problem', 'issue', 'broken', 'not working', 'help', 'deadline']
        content_lower = f"{context.subject} {context.content}".lower()
        
        urgency_matches = sum(1 for word in urgent_words if word in content_lower)
        score += min(urgency_matches * 2, 4)
        
        # Sender importance (VIP clients, suppliers)
        vip_domains = ['@important-client.cz', '@major-supplier.com', '@vip-customer.eu']
        if any(domain in context.sender for domain in vip_domains):
            score += 2
        
        # Time sensitivity
        if 'today' in content_lower or 'tomorrow' in content_lower:
            score += 1
        
        # Multiple participants (group decisions)
        if len(context.participants) > 3:
            score += 1
        
        return min(score, 10)
    
    def _analyze_relationships(self, email_contexts: List[EmailContext]):
        """Analyze relationships between different email threads"""
        # Build keyword maps for relationship detection
        for context in email_contexts:
            # Extract key entities (companies, products, order numbers)
            entities = self._extract_entities(context.content)
            
            # Find related threads
            related = []
            for other_context in email_contexts:
                if other_context.thread_id != context.thread_id:
                    if self._threads_related(context, other_context, entities):
                        related.append(other_context.thread_id)
            
            context.related_threads = related
    
    def _extract_entities(self, content: str) -> Dict[str, List[str]]:
        """Extract business entities from email content"""
        entities = {
            'companies': [],
            'products': [],
            'order_numbers': [],
            'amounts': []
        }
        
        # Simple entity extraction (in production, use NLP)
        words = content.lower().split()
        
        # Look for order numbers (pattern: ORD-12345, #12345, etc.)
        import re
        order_patterns = [r'ord-\d+', r'#\d+', r'order\s+\d+', r'objednávka\s+\d+']
        for pattern in order_patterns:
            matches = re.findall(pattern, content.lower())
            entities['order_numbers'].extend(matches)
        
        # Look for amounts (CZK, EUR, $)
        amount_patterns = [r'\d+[,\s]*\d*\s*czk', r'\d+[,\s]*\d*\s*eur', r'\$\d+']
        for pattern in amount_patterns:
            matches = re.findall(pattern, content.lower())
            entities['amounts'].extend(matches)
        
        return entities
    
    def _threads_related(self, context1: EmailContext, context2: EmailContext, entities1: Dict) -> bool:
        """Determine if two email threads are related"""
        # Same participants
        common_participants = set(context1.participants) & set(context2.participants)
        if len(common_participants) > 1:
            return True
        
        # Common order numbers or entities
        entities2 = self._extract_entities(context2.content)
        
        # Check for common order numbers
        if entities1['order_numbers'] and entities2['order_numbers']:
            if set(entities1['order_numbers']) & set(entities2['order_numbers']):
                return True
        
        # Check for common amounts
        if entities1['amounts'] and entities2['amounts']:
            if set(entities1['amounts']) & set(entities2['amounts']):
                return True
        
        # Similar subjects (basic similarity)
        subject_words1 = set(context1.subject.lower().split())
        subject_words2 = set(context2.subject.lower().split())
        common_words = subject_words1 & subject_words2
        if len(common_words) >= 2:
            return True
        
        return False
    
    def draft_intelligent_responses(self, email_contexts: List[EmailContext]) -> Dict:
        """Draft context-aware responses for all emails"""
        responses = {
            'immediate_responses': [],
            'related_group_responses': [],
            'follow_up_actions': []
        }
        
        # Group related emails
        processed_threads = set()
        
        for context in email_contexts:
            if context.thread_id in processed_threads:
                continue
            
            if context.related_threads:
                # Handle as group
                related_contexts = [context]
                for thread_id in context.related_threads:
                    related_context = next((ctx for ctx in email_contexts if ctx.thread_id == thread_id), None)
                    if related_context:
                        related_contexts.append(related_context)
                        processed_threads.add(thread_id)
                
                group_response = self._draft_group_response(related_contexts)
                responses['related_group_responses'].append(group_response)
                
            else:
                # Handle individually
                individual_response = self._draft_individual_response(context)
                responses['immediate_responses'].append(individual_response)
            
            processed_threads.add(context.thread_id)
        
        return responses
    
    def _draft_individual_response(self, context: EmailContext) -> Dict:
        """Draft response for individual email"""
        # Analyze content and determine response type
        response_type = self._determine_response_type(context.content)
        
        draft = self._generate_response_template(context, response_type)
        
        return {
            'thread_id': context.thread_id,
            'sender': context.sender,
            'subject': f"Re: {context.subject}",
            'urgency': context.urgency_score,
            'response_type': response_type,
            'draft_content': draft,
            'reasoning': f"Individual response to {context.sender} regarding {response_type}"
        }
    
    def _draft_group_response(self, related_contexts: List[EmailContext]) -> Dict:
        """Draft coordinated responses for related email threads"""
        # Analyze the relationship and create coordinated response
        main_context = max(related_contexts, key=lambda x: x.urgency_score)
        
        # Determine if this is client-supplier coordination
        is_client_supplier = self._is_client_supplier_coordination(related_contexts)
        
        if is_client_supplier:
            return self._draft_client_supplier_coordination(related_contexts)
        else:
            return self._draft_general_group_response(related_contexts)
    
    def _is_client_supplier_coordination(self, contexts: List[EmailContext]) -> bool:
        """Detect if this is client-supplier coordination scenario"""
        # Simple heuristic: different domains, content mentions orders/delivery/products
        domains = set()
        for context in contexts:
            domain = context.sender.split('@')[-1] if '@' in context.sender else ''
            domains.add(domain)
        
        # Multiple domains + business keywords
        business_keywords = ['order', 'delivery', 'product', 'supplier', 'client', 'objednávka', 'dodávka']
        content = ' '.join([ctx.content for ctx in contexts]).lower()
        
        return len(domains) > 1 and any(keyword in content for keyword in business_keywords)
    
    def _draft_client_supplier_coordination(self, contexts: List[EmailContext]) -> Dict:
        """Draft coordinated client-supplier response"""
        # Find client and supplier
        client_context = None
        supplier_context = None
        
        for context in contexts:
            content_lower = context.content.lower()
            if any(word in content_lower for word in ['need', 'order', 'request', 'when']):
                client_context = context
            elif any(word in content_lower for word in ['deliver', 'supply', 'available', 'stock']):
                supplier_context = context
        
        # Draft coordinated responses
        responses = []
        
        if client_context:
            client_response = f"""Dear {client_context.sender.split('@')[0]},

Thank you for your inquiry. I'm coordinating with our supplier to get you the exact information you need.

I'll have a detailed response within 4 business hours with:
- Availability confirmation
- Delivery timeline  
- Pricing details

Best regards,
Petr Svejkovsky
Premium Gastro"""
            
            responses.append({
                'to': client_context.sender,
                'subject': f"Re: {client_context.subject}",
                'content': client_response,
                'priority': 'high'
            })
        
        if supplier_context:
            supplier_response = f"""Hello {supplier_context.sender.split('@')[0]},

I need urgent confirmation for client order:

[Details from client request]

Please confirm:
1. Availability
2. Delivery timeline
3. Final pricing

Client is waiting for response.

Thanks,
Petr Svejkovsky
Premium Gastro"""
            
            responses.append({
                'to': supplier_context.sender,
                'subject': f"Re: {supplier_context.subject}",
                'content': supplier_response,
                'priority': 'urgent'
            })
        
        return {
            'coordination_type': 'client_supplier',
            'responses': responses,
            'reasoning': 'Coordinated client-supplier communication - client inquiry matched with supplier capabilities'
        }
    
    def _determine_response_type(self, content: str) -> str:
        """Determine what type of response is needed"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['meeting', 'call', 'schedule', 'kalendář']):
            return 'meeting_request'
        elif any(word in content_lower for word in ['quote', 'price', 'cost', 'nabídka', 'cena']):
            return 'quote_request'
        elif any(word in content_lower for word in ['delivery', 'order', 'dodávka', 'objednávka']):
            return 'order_inquiry'
        elif any(word in content_lower for word in ['problem', 'issue', 'broken', 'problém']):
            return 'support_request'
        elif any(word in content_lower for word in ['thank', 'thanks', 'děkuji']):
            return 'acknowledgment'
        else:
            return 'general_inquiry'
    
    def _generate_response_template(self, context: EmailContext, response_type: str) -> str:
        """Generate appropriate response template"""
        sender_name = context.sender.split('@')[0]
        
        templates = {
            'meeting_request': f"""Dear {sender_name},

Thank you for reaching out regarding a meeting.

I'm checking my calendar and will confirm available time slots within 2 hours.
Would you prefer video call or in-person meeting?

Best regards,
Petr Svejkovsky
Premium Gastro""",

            'quote_request': f"""Dear {sender_name},

Thank you for your inquiry about pricing.

I'm preparing a detailed quote and will send it within 4 business hours.
If you have any specific requirements or deadlines, please let me know.

Best regards,
Petr Svejkovsky
Premium Gastro""",

            'order_inquiry': f"""Dear {sender_name},

Thank you for your order inquiry.

I'm checking availability and delivery options immediately.
You'll receive detailed confirmation within 4 business hours.

Best regards,
Petr Svejkovsky
Premium Gastro""",

            'support_request': f"""Dear {sender_name},

Thank you for reporting this issue. I understand the urgency.

I'm addressing this immediately and will provide an update within 2 hours.
If this is critical, please call me directly.

Best regards,
Petr Svejkovsky
Premium Gastro""",

            'general_inquiry': f"""Dear {sender_name},

Thank you for your message.

I'm reviewing your inquiry and will provide a detailed response within 4 business hours.

Best regards,
Petr Svejkovsky
Premium Gastro"""
        }
        
        return templates.get(response_type, templates['general_inquiry'])

def main():
    """Run Missive AI Assistant"""
    print("📧 MISSIVE AI ASSISTANT - CONTEXT-AWARE EMAIL INTELLIGENCE")
    print("=" * 70)
    
    assistant = MissiveAIAssistant()
    
    # Get unread emails
    print("📥 Fetching unread emails...")
    email_contexts = assistant.get_unread_emails()
    
    print(f"   Found {len(email_contexts)} unread emails")
    
    if not email_contexts:
        print("✅ No unread emails found!")
        return
    
    # Draft intelligent responses
    print("\n🧠 Analyzing relationships and drafting responses...")
    responses = assistant.draft_intelligent_responses(email_contexts)
    
    print(f"\n📊 RESPONSE SUMMARY:")
    print(f"   Individual Responses: {len(responses['immediate_responses'])}")
    print(f"   Related Group Responses: {len(responses['related_group_responses'])}")
    
    # Show immediate responses
    if responses['immediate_responses']:
        print(f"\n📧 IMMEDIATE RESPONSES READY:")
        for i, response in enumerate(responses['immediate_responses'][:3], 1):
            print(f"   {i}. [{response['urgency']}/10] {response['sender']}")
            print(f"      Subject: {response['subject']}")
            print(f"      Type: {response['response_type']}")
            print()
    
    # Show group coordination
    if responses['related_group_responses']:
        print(f"\n🔗 COORDINATED RESPONSES:")
        for group in responses['related_group_responses']:
            if group['coordination_type'] == 'client_supplier':
                print(f"   🎯 Client-Supplier Coordination:")
                print(f"      Responses: {len(group['responses'])}")
                print(f"      Reasoning: {group['reasoning']}")
            print()
    
    # Save responses for immediate use
    with open('/tmp/email_responses.json', 'w') as f:
        json.dump(responses, f, indent=2)
    
    print(f"💾 All responses saved to: /tmp/email_responses.json")
    print(f"🎯 Ready for immediate deployment in Missive!")

if __name__ == "__main__":
    main()