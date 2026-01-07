#!/usr/bin/env python3
"""
INTELLIGENT EMAIL PROCESSOR - COMPLETE AUTOMATION SYSTEM
Combines Supabase VIP analysis + SaneBox filtering +
Lindy AI processing + Missive integration.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass

@dataclass
class EmailProcessingResult:
    email_id: str
    sender: str
    subject: str
    classification: str
    priority_level: int
    vip_status: bool
    urgency_detected: bool
    suggested_response: str
    processing_confidence: float


class IntelligentEmailProcessor:
    """Complete email intelligence system using all Premium Gastro data"""

    def __init__(self):
        # Initialize logging first
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Email classification thresholds
        self.thresholds = {
            'vip_score_minimum': 40,
            'high_priority_minimum': 70,
            'urgency_confidence_minimum': 0.7,
            'processing_confidence_minimum': 0.8
        }

        # Load VIP analysis results
        self.load_vip_analysis()

        # Missive API setup (if available)
        self.missive_token = os.getenv('MISSIVE_API_TOKEN')
        self.missive_org = os.getenv('MISSIVE_ORG_ID')

    def load_vip_analysis(self):
        """Load the generated VIP analysis data"""
        try:
            vip_file = '/tmp/vip_analysis_complete.json'
            with open(
                    vip_file, 'r', encoding='utf-8') as f:
                self.vip_data = json.load(f)

            # Create lookup dictionaries for fast processing
            self.vip_emails = {}
            self.vip_domains = set()

            for contact in self.vip_data['vip_contacts']:
                email = contact['email'].lower()
                self.vip_emails[email] = contact

                if '@' in email:
                    domain = email.split('@')[1]
                    self.vip_domains.add(domain)

            # Urgency keywords from analysis
            self.urgency_keywords = []
            for pattern in self.vip_data['urgency_patterns']:
                if pattern['priority_level'] >= 7:
                    self.urgency_keywords.extend(pattern['keywords'])

            self.urgency_keywords = list(set(self.urgency_keywords))

            msg = (
                f"Loaded VIP data: {len(self.vip_emails)} contacts, "
                f"{len(self.urgency_keywords)} urgency keywords"
            )
            self.logger.info(msg)

        except Exception as e:
            self.logger.error(f"Failed to load VIP analysis: {e}")
            self.vip_data = {'vip_contacts': [], 'urgency_patterns': []}
            self.vip_emails = {}
            self.vip_domains = set()
            self.urgency_keywords = []

    def classify_email(
            self, sender: str, subject: str, content: str
    ) -> EmailProcessingResult:
        """Classify email using all intelligence layers"""

        # Step 1: VIP Detection
        vip_status, vip_contact = self._detect_vip_status(sender)

        # Step 2: Urgency Detection
        urgency_detected, urgency_score = self._detect_urgency(
            subject, content)

        # Step 3: Content Classification
        classification = self._classify_content(
            subject, content, vip_status, urgency_detected)

        # Step 4: Priority Calculation
        priority_level = self._calculate_priority(
            vip_status, urgency_score, classification, vip_contact)

        # Step 5: Response Generation
        suggested_response = self._generate_response_suggestion(
            sender, subject, content, classification, vip_status,
            urgency_detected
        )

        # Step 6: Confidence Assessment
        confidence = self._assess_confidence(
            vip_status, urgency_detected, classification)

        return EmailProcessingResult(
            email_id=f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            sender=sender,
            subject=subject,
            classification=classification,
            priority_level=priority_level,
            vip_status=vip_status,
            urgency_detected=urgency_detected,
            suggested_response=suggested_response,
            processing_confidence=confidence
        )

    def _detect_vip_status(
            self, sender: str) -> tuple[bool, Optional[Dict]]:
        """Detect if sender is VIP based on Supabase analysis"""
        sender_lower = sender.lower()

        # Direct email match
        if sender_lower in self.vip_emails:
            contact = self.vip_emails[sender_lower]
            return True, contact

        # Domain match for VIP business domains
        if '@' in sender_lower:
            domain = sender_lower.split('@')[1]
            if domain in self.vip_domains:
                # Find any contact from this domain
                for email, contact in self.vip_emails.items():
                    if domain in email:
                        return True, contact

        return False, None

    def _detect_urgency(
            self, subject: str, content: str) -> tuple[bool, float]:
        """Detect urgency using multi-language patterns"""
        text = f"{subject} {content}".lower()

        urgency_matches = 0
        total_checks = len(self.urgency_keywords)

        if total_checks == 0:
            return False, 0.0

        # Count matches
        for keyword in self.urgency_keywords:
            if keyword.lower() in text:
                urgency_matches += 1

        urgency_score = urgency_matches / total_checks

        # Additional urgency indicators
        crisis_words = [
            'emergency', 'broken', 'nefunguje', 'kritické', 'notfall', 'asap'
        ]
        for word in crisis_words:
            if word in text:
                urgency_score += 0.3

        # Time-sensitive words
        time_words = [
            'today', 'dnes', 'heute', 'immediately', 'okamžitě', 'sofort'
        ]
        for word in time_words:
            if word in text:
                urgency_score += 0.2

        min_urgency = self.thresholds['urgency_confidence_minimum']
        urgency_detected = urgency_score >= min_urgency

        return urgency_detected, min(urgency_score, 1.0)

    def _classify_content(
            self, subject: str, content: str, is_vip: bool,
            is_urgent: bool) -> str:
        """Classify email content type"""
        text = f"{subject} {content}".lower()

        # Business classifications
        financial_words = [
            'invoice', 'faktura', 'payment', 'platba', 'bill'
        ]
        if any(word in text for word in financial_words):
            return 'financial'

        meeting_words = [
            'meeting', 'call', 'schůzka', 'kalendář', 'calendar'
        ]
        if any(word in text for word in meeting_words):
            return 'meeting_request'

        order_words = ['order', 'objednávka', 'delivery', 'dodávka']
        if any(word in text for word in order_words):
            return 'order_inquiry'

        quote_words = ['quote', 'nabídka', 'price', 'cena']
        if any(word in text for word in quote_words):
            return 'quote_request'

        problem_words = [
            'problem', 'issue', 'broken', 'problém', 'nefunguje'
        ]
        if any(word in text for word in problem_words):
            return 'support_request'

        thank_words = ['thank', 'thanks', 'děkuji', 'danke']
        if any(word in text for word in thank_words):
            return 'acknowledgment'

        # Default classification based on status
        if is_urgent:
            return 'urgent_inquiry'
        elif is_vip:
            return 'vip_communication'
        else:
            return 'general_inquiry'

    def _calculate_priority(
            self, is_vip: bool, urgency_score: float,
            classification: str,
            vip_contact: Optional[Dict]) -> int:
        """Calculate priority level 1-10"""
        priority = 5  # Base priority

        # VIP status boost
        if is_vip and vip_contact:
            vip_score = vip_contact.get('vip_score', 50)
            if vip_score >= 90:
                priority += 3
            elif vip_score >= 70:
                priority += 2
            else:
                priority += 1

        # Urgency boost
        priority += int(urgency_score * 3)

        # Classification-specific priority
        classification_priorities = {
            'financial': 2,
            'support_request': 3,
            'urgent_inquiry': 3,
            'meeting_request': 1,
            'order_inquiry': 2,
            'quote_request': 1,
            'vip_communication': 1,
            'acknowledgment': -1,
            'general_inquiry': 0
        }

        priority += classification_priorities.get(classification, 0)

        return max(1, min(priority, 10))

    def _generate_response_suggestion(
            self, sender: str, subject: str, content: str,
            classification: str, is_vip: bool,
            is_urgent: bool) -> str:
        """Generate intelligent response suggestions"""

        sender_name = sender.split('@')[0] if '@' in sender else sender

        # Response templates based on classification
        templates = {
            'financial': f"""Dear {sender_name},

Thank you for your financial inquiry. I'm reviewing the details
immediately.

You'll receive a detailed response within 2 business hours.

Best regards,
Petr Svejkovsky
Premium Gastro""",

            'support_request': f"""Dear {sender_name},

Thank you for reporting this issue. I understand the urgency and
am addressing it immediately.

I'll provide an update within 1 hour. If this is critical,
please call me directly.

Best regards,
Petr Svejkovsky
Premium Gastro""",

            'meeting_request': f"""Dear {sender_name},

Thank you for your meeting request. I'm checking my calendar
and will confirm available time slots within 2 hours.

Would you prefer video call or in-person meeting?

Best regards,
Petr Svejkovsky
Premium Gastro""",

            'order_inquiry': f"""Dear {sender_name},

Thank you for your order inquiry. I'm checking availability
and delivery options immediately.

You'll receive detailed confirmation within 4 business hours.

Best regards,
Petr Svejkovsky
Premium Gastro""",

            'quote_request': f"""Dear {sender_name},

Thank you for your quote request. I'm preparing a detailed proposal.

You'll receive the quote within 4 business hours. If you have any
specific requirements, please let me know.

Best regards,
Petr Svejkovsky
Premium Gastro""",

            'vip_communication': f"""Dear {sender_name},

Thank you for your message. As a valued client, I'm prioritizing
your inquiry.

I'll provide a detailed response within 2 business hours.

Best regards,
Petr Svejkovsky
Premium Gastro""",

            'urgent_inquiry': f"""Dear {sender_name},

Thank you for your urgent message. I'm addressing this immediately.

You'll receive an update within 1 hour.

Best regards,
Petr Svejkovsky
Premium Gastro""",

            'acknowledgment': f"""Dear {sender_name},

Thank you for your kind message. I appreciate your feedback.

Best regards,
Petr Svejkovsky
Premium Gastro""",

            'general_inquiry': f"""Dear {sender_name},

Thank you for your inquiry. I'm reviewing your message and will
provide a detailed response within 4 business hours.

Best regards,
Petr Svejkovsky
Premium Gastro"""
        }

        default_template = templates['general_inquiry']
        base_response = templates.get(classification, default_template)

        # Add urgency note if urgent
        if is_urgent:
            base_response = base_response.replace(
                "Best regards,", "URGENT PRIORITY - Best regards,")

        # Add VIP note if VIP
        if is_vip:
            base_response = base_response.replace(
                "Thank you for", "Thank you for your valued")

        return base_response

    def _assess_confidence(
            self, is_vip: bool, is_urgent: bool,
            classification: str) -> float:
        """Assess processing confidence"""
        confidence = 0.7  # Base confidence

        # VIP detection adds confidence
        if is_vip:
            confidence += 0.2

        # Clear classifications add confidence
        high_confidence_classes = [
            'financial', 'support_request', 'meeting_request'
        ]
        if classification in high_confidence_classes:
            confidence += 0.1

        # Urgency detection adds confidence
        if is_urgent:
            confidence += 0.1

        return min(confidence, 1.0)

    def process_email_batch(
            self, emails: List[Dict]) -> List[EmailProcessingResult]:
        """Process multiple emails with intelligent sorting"""
        results = []

        for email in emails:
            sender = email.get('sender', '')
            subject = email.get('subject', '')
            content = email.get('content', '')

            result = self.classify_email(sender, subject, content)
            results.append(result)

        # Sort by priority (highest first)
        results.sort(key=lambda x: x.priority_level, reverse=True)

        return results

    def export_processing_rules(self) -> Dict:
        """Export rules for SaneBox and Lindy integration"""

        min_score = self.thresholds['high_priority_minimum']
        top_vip_emails = [
            contact['email']
            for contact in self.vip_data['vip_contacts'][:50]
            if contact['vip_score'] >= min_score
        ]

        return {
            'sanebox_rules': {
                'vip_whitelist': top_vip_emails,
                'urgency_keywords': self.urgency_keywords[:30],
                'business_domains': list(self.vip_domains),
                'auto_archive_patterns': [
                    'newsletter@', 'noreply@', 'no-reply@', 'marketing@',
                    'notification@', 'automated@'
                ]
            },
            'lindy_processing_rules': {
                'process_only_folders': [
                    'Inbox', '@SanePriority', '@SaneMoney', '@SaneMeetings'
                ],
                'ignore_folders': ['@SaneLater', '@SaneNews', '@SaneCC'],
                'max_emails_per_day': 50,
                'priority_threshold': 6
            },
            'response_automation': {
                'auto_respond_to_vips': True,
                'auto_respond_to_urgent': True,
                'require_approval_threshold': 8
            }
        }


def main():
    """Demonstrate intelligent email processing"""
    print("🧠 INTELLIGENT EMAIL PROCESSOR - COMPLETE AUTOMATION")
    print("=" * 60)

    processor = IntelligentEmailProcessor()

    # Test emails
    test_emails = [
        {
            'sender': 'faktury@zatisigroup.cz',
            'subject': 'Urgent: Invoice payment required',
            'content': (
                'We need immediate payment for invoice #12345. '
                'This is overdue and requires attention.'
            )
        },
        {
            'sender': 'vanduch@montycon.cz',
            'subject': 'Meeting request for next week',
            'content': (
                'Could we schedule a meeting to discuss '
                'the new menu items?'
            )
        },
        {
            'sender': 'spam@marketing.com',
            'subject': 'Special offer just for you!',
            'content': 'Buy now and save 50% on our amazing products!'
        },
        {
            'sender': 'info@golf-ski.eu',
            'subject': 'Problem with delivery',
            'content': (
                'Our guests are waiting and the delivery is not here. '
                'Please help ASAP!'
            )
        }
    ]

    print(f"\n📧 Processing {len(test_emails)} test emails...")
    results = processor.process_email_batch(test_emails)

    print("\n📊 PROCESSING RESULTS (sorted by priority):")
    for i, result in enumerate(results, 1):
        vip_status = "⭐ VIP" if result.vip_status else "Standard"
        urgency_status = "🚨 URGENT" if result.urgency_detected else "Normal"

        priority_msg = (
            f"\n{i}. Priority {result.priority_level}/10 | "
            f"{vip_status} | {urgency_status}")
        print(priority_msg)
        print(f"   From: {result.sender}")
        print(f"   Subject: {result.subject}")
        print(f"   Classification: {result.classification}")
        print(f"   Confidence: {result.processing_confidence:.1%}")
        action_preview = result.suggested_response.split('.')[0]
        print(f"   Suggested Action: {action_preview}...")

    # Export rules
    rules = processor.export_processing_rules()
    with open('/tmp/email_processing_rules.json', 'w') as f:
        json.dump(rules, f, indent=2)

    print("\n✅ Email processing complete!")
    print("📁 Processing rules exported to: /tmp/email_processing_rules.json")
    print(f"🎯 VIP contacts loaded: {len(processor.vip_emails)}")
    print(f"🚨 Urgency keywords: {len(processor.urgency_keywords)}")
    print("\n🚀 READY FOR PRODUCTION EMAIL AUTOMATION!")


if __name__ == "__main__":
    main()
