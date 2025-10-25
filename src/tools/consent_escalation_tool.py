"""
Consent and Escalation Tool for LiveKit Agents
"""

import os
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass
from livekit.agents import function_tool, RunContext
from datetime import datetime

logger = logging.getLogger("consent_escalation")


@dataclass
class ConsentRecord:
    """Record of consent given by user"""

    consent_type: str
    given: bool
    timestamp: datetime
    user_id: str
    details: str = ""


@dataclass
class EscalationRecord:
    """Record of escalation events"""

    escalation_type: str
    reason: str
    timestamp: datetime
    user_id: str
    status: str = "pending"  # pending, resolved, cancelled
    assigned_to: Optional[str] = None


class ConsentEscalationTool:
    """Tool for handling consent and escalation in healthcare/elderly care scenarios"""

    def __init__(self):
        self.consent_records: List[ConsentRecord] = []
        self.escalation_records: List[EscalationRecord] = []

        # Emergency contacts
        self.emergency_contacts = {
            "doctor": "+1234567890",
            "nurse": "+1234567891",
            "family": "+1234567892",
            "emergency": "911",
        }

        # Escalation levels
        self.escalation_levels = {
            "low": "family member",
            "medium": "nurse or doctor",
            "high": "emergency services",
            "critical": "immediate emergency response",
        }

    @function_tool
    async def request_consent(
        self, context: RunContext, consent_type: str, purpose: str = ""
    ):
        """Request consent from the user for various activities.

        Args:
            consent_type: Type of consent (recording, medical, data_sharing, etc.)
            purpose: Purpose for requesting consent
        """
        if not consent_type or consent_type.strip() == "":
            return "What type of consent do you need?"

        user_id = getattr(context, "room", {}).get("name", "unknown")

        # Check if consent already given
        existing_consent = self._get_latest_consent(user_id, consent_type)
        if existing_consent and existing_consent.given:
            return (
                f"You've already given consent for {consent_type}. Is this still okay?"
            )

        # Request consent
        if consent_type == "recording":
            return f"I'd like to record our conversation for quality assurance and to help me remember our chats. Is that okay with you?"
        elif consent_type == "medical":
            return f"To help you better, I'd like to ask about your health and share information with your care team. Is that okay?"
        elif consent_type == "data_sharing":
            return f"I'd like to share information about our conversations with your family members to keep them updated. Is that okay?"
        else:
            return f"I need your permission to {consent_type}. {purpose} Is that okay?"

    @function_tool
    async def record_consent(
        self, context: RunContext, consent_type: str, given: bool, details: str = ""
    ):
        """Record the user's consent decision.

        Args:
            consent_type: Type of consent
            given: Whether consent was given (true/false)
            details: Additional details about the consent
        """
        if not consent_type or consent_type.strip() == "":
            return "What type of consent are you recording?"

        user_id = getattr(context, "room", {}).get("name", "unknown")

        # Create consent record
        consent_record = ConsentRecord(
            consent_type=consent_type,
            given=given,
            timestamp=datetime.now(),
            user_id=user_id,
            details=details,
        )

        self.consent_records.append(consent_record)

        if given:
            logger.info(f"Consent given for {consent_type} by {user_id}")
            return f"Thank you! I've recorded your consent for {consent_type}."
        else:
            logger.info(f"Consent denied for {consent_type} by {user_id}")
            return f"I understand. I've noted that you don't want to give consent for {consent_type}."

    @function_tool
    async def check_consent(self, context: RunContext, consent_type: str):
        """Check if user has given consent for a specific activity.

        Args:
            consent_type: Type of consent to check
        """
        if not consent_type or consent_type.strip() == "":
            return "What type of consent should I check?"

        user_id = getattr(context, "room", {}).get("name", "unknown")
        consent = self._get_latest_consent(user_id, consent_type)

        if not consent:
            return f"You haven't given consent for {consent_type} yet."
        elif consent.given:
            return f"Yes, you've given consent for {consent_type}."
        else:
            return f"No, you haven't given consent for {consent_type}."

    @function_tool
    async def escalate_concern(
        self,
        context: RunContext,
        concern_type: str,
        severity: str,
        description: str = "",
    ):
        """Escalate a concern to appropriate personnel.

        Args:
            concern_type: Type of concern (medical, safety, emotional, etc.)
            severity: Severity level (low, medium, high, critical)
            description: Description of the concern
        """
        if not concern_type or not severity:
            return "What type of concern needs to be escalated and how severe is it?"

        user_id = getattr(context, "room", {}).get("name", "unknown")

        # Create escalation record
        escalation = EscalationRecord(
            escalation_type=concern_type,
            reason=description,
            timestamp=datetime.now(),
            user_id=user_id,
            status="pending",
        )

        self.escalation_records.append(escalation)

        # Determine appropriate response based on severity
        if severity == "critical":
            logger.critical(f"CRITICAL escalation: {concern_type} - {description}")
            return f"I'm immediately escalating this critical {concern_type} concern. Emergency services will be contacted right away."
        elif severity == "high":
            logger.warning(f"HIGH priority escalation: {concern_type} - {description}")
            return f"I'm escalating this {concern_type} concern to your doctor and family immediately."
        elif severity == "medium":
            logger.info(f"MEDIUM priority escalation: {concern_type} - {description}")
            return f"I'm escalating this {concern_type} concern to your care team. They'll follow up soon."
        else:  # low
            logger.info(f"LOW priority escalation: {concern_type} - {description}")
            return f"I've noted this {concern_type} concern and will share it with your family during their next check-in."

    @function_tool
    async def emergency_contact(
        self, context: RunContext, contact_type: str, message: str = ""
    ):
        """Contact emergency services or family immediately.

        Args:
            contact_type: Type of contact (doctor, nurse, family, emergency)
            message: Message to convey
        """
        if not contact_type or contact_type.strip() == "":
            return "Who should I contact for you?"

        user_id = getattr(context, "room", {}).get("name", "unknown")

        if contact_type.lower() in self.emergency_contacts:
            contact_number = self.emergency_contacts[contact_type.lower()]

            # Create escalation record
            escalation = EscalationRecord(
                escalation_type="emergency_contact",
                reason=f"Contacted {contact_type}: {message}",
                timestamp=datetime.now(),
                user_id=user_id,
                status="in_progress",
                assigned_to=contact_type,
            )
            self.escalation_records.append(escalation)

            logger.warning(f"Emergency contact initiated: {contact_type} for {user_id}")
            return f"I'm contacting {contact_type} right now at {contact_number}. They'll be here soon."
        else:
            return f"I don't have contact information for {contact_type}. Let me try your family or doctor instead."

    @function_tool
    async def check_escalations(self, context: RunContext):
        """Check status of pending escalations."""
        user_id = getattr(context, "room", {}).get("name", "unknown")

        pending_escalations = [
            e
            for e in self.escalation_records
            if e.user_id == user_id and e.status == "pending"
        ]

        if not pending_escalations:
            return "You don't have any pending escalations right now."

        escalation_list = []
        for esc in pending_escalations:
            escalation_list.append(f"{esc.escalation_type} - {esc.reason}")

        return f"You have {len(pending_escalations)} pending escalations: {'; '.join(escalation_list)}"

    def _get_latest_consent(
        self, user_id: str, consent_type: str
    ) -> Optional[ConsentRecord]:
        """Get the latest consent record for a user and consent type"""
        user_consents = [
            c
            for c in self.consent_records
            if c.user_id == user_id and c.consent_type == consent_type
        ]

        if not user_consents:
            return None

        # Return the most recent consent
        return max(user_consents, key=lambda x: x.timestamp)

    def get_consent_summary(self, user_id: str) -> Dict[str, bool]:
        """Get summary of all consents for a user"""
        user_consents = [c for c in self.consent_records if c.user_id == user_id]

        summary = {}
        for consent in user_consents:
            # Only keep the latest consent for each type
            if consent.consent_type not in summary:
                summary[consent.consent_type] = consent.given
            else:
                # If we already have this consent type, check if this one is more recent
                existing = self._get_latest_consent(user_id, consent.consent_type)
                if existing and consent.timestamp > existing.timestamp:
                    summary[consent.consent_type] = consent.given

        return summary
