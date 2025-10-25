import logging
import os
from typing import Dict, List, Optional
from mailjet_rest import Client
from livekit.agents import function_tool, RunContext

logger = logging.getLogger(__name__)


class MailjetTool:
    """Tool for sending emails via Mailjet API"""

    def __init__(self):
        self.api_key = os.getenv("MAILJET_API_KEY")
        self.secret_key = os.getenv("MAILJET_SECRET_KEY")
        self.from_email = os.getenv("MAILJET_FROM_EMAIL", "noreply@yourdomain.com")
        self.from_name = os.getenv("MAILJET_FROM_NAME", "Heather Assistant")

        if not all([self.api_key, self.secret_key]):
            logger.warning(
                "Mailjet credentials not found. Email sending will not be available."
            )
            self.client = None
        else:
            self.client = Client(auth=(self.api_key, self.secret_key))
            logger.info("Mailjet tool initialized successfully")

    @function_tool()
    async def send_email(
        self,
        ctx: RunContext,
        to_emails: List[str],
        subject: str,
        text_content: str,
        html_content: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Send an email using Mailjet API

        Args:
            to_emails: List of recipient email addresses
            subject: Email subject line
            text_content: Plain text content of the email
            html_content: Optional HTML content of the email
            reply_to: Optional reply-to email address

        Returns:
            Dict with success status and message
        """
        if not self.client:
            return {
                "success": "false",
                "message": "Mailjet not configured - missing API credentials",
            }

        try:
            # Prepare recipients
            recipients = []
            for email in to_emails:
                recipients.append(
                    {
                        "Email": email,
                        "Name": email.split("@")[0],  # Use email prefix as name
                    }
                )

            # Prepare email data
            email_data = {
                "Messages": [
                    {
                        "FromEmail": self.from_email,
                        "FromName": self.from_name,
                        "Recipients": recipients,
                        "Subject": subject,
                        "TextPart": text_content,
                        "HTMLPart": html_content or text_content,
                    }
                ]
            }

            # Add reply-to if specified
            if reply_to:
                email_data["Messages"][0]["ReplyTo"] = {
                    "Email": reply_to,
                    "Name": reply_to.split("@")[0],
                }

            # Send email
            result = self.client.send.create(data=email_data)

            if result.status_code == 200:
                response_data = result.json()
                message_id = (
                    response_data.get("Messages", [{}])[0]
                    .get("To", [{}])[0]
                    .get("MessageID", "unknown")
                )

                logger.info(f"Email sent successfully. Message ID: {message_id}")
                return {
                    "success": "true",
                    "message": f"Email sent successfully to {len(to_emails)} recipients",
                    "message_id": message_id,
                }
            else:
                error_text = result.text if hasattr(result, 'text') else str(result)
                error_msg = f"Mailjet API error: {result.status_code} - {error_text}"
                logger.error(error_msg)
                return {"success": "false", "message": error_msg}

        except Exception as e:
            error_msg = f"Error sending email via Mailjet: {e}"
            logger.error(error_msg)
            return {"success": "false", "message": error_msg}

    @function_tool()
    async def send_emergency_notification(
        self,
        ctx: RunContext,
        emergency_type: str,
        details: str,
        timestamp: str,
        recipient_emails: List[str],
    ) -> Dict[str, str]:
        """
        Send an emergency notification email with formatted content

        Args:
            emergency_type: Type of emergency (e.g., "fall", "medical", "urgent")
            details: Details about the emergency
            timestamp: When the emergency occurred
            recipient_emails: List of emergency contact email addresses

        Returns:
            Dict with success status and message
        """
        subject = f"EMERGENCY ALERT - Maggie Thompson - {emergency_type.upper()}"

        # Plain text content
        text_content = f"""
EMERGENCY ALERT - MAGGIE THOMPSON
================================

TIMESTAMP: {timestamp}
EMERGENCY TYPE: {emergency_type.upper()}
STATUS: ACTIVE

DETAILS:
{details}

This is an automated emergency notification from Heather, Maggie's AI assistant.
Please check on Maggie immediately.

---
Heather AI Assistant
Emergency Notification System
        """.strip()

        # HTML content for better formatting
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Emergency Alert</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #ff4444; color: white; padding: 15px; border-radius: 5px; }}
        .content {{ margin: 20px 0; }}
        .details {{ background-color: #f5f5f5; padding: 15px; border-left: 4px solid #ff4444; }}
        .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚨 EMERGENCY ALERT - MAGGIE THOMPSON</h1>
    </div>
    
    <div class="content">
        <p><strong>TIMESTAMP:</strong> {timestamp}</p>
        <p><strong>EMERGENCY TYPE:</strong> {emergency_type.upper()}</p>
        <p><strong>STATUS:</strong> <span style="color: #ff4444;">ACTIVE</span></p>
        
        <div class="details">
            <h3>DETAILS:</h3>
            <p>{details}</p>
        </div>
        
        <p><strong>Action Required:</strong> Please check on Maggie immediately.</p>
    </div>
    
    <div class="footer">
        <p>This is an automated emergency notification from Heather, Maggie's AI assistant.</p>
        <p>Heather AI Assistant | Emergency Notification System</p>
    </div>
</body>
</html>
        """.strip()

        return await self.send_email(
            ctx=ctx,
            to_emails=recipient_emails,
            subject=subject,
            text_content=text_content,
            html_content=html_content,
        )

    @function_tool()
    async def send_daily_summary(
        self, ctx: RunContext, summary_data: Dict, recipient_emails: List[str]
    ) -> Dict[str, str]:
        """
        Send a daily summary email about Maggie's activities

        Args:
            summary_data: Dictionary containing summary information
            recipient_emails: List of family member email addresses

        Returns:
            Dict with success status and message
        """
        subject = (
            f"📊 Daily Summary - Maggie Thompson - {summary_data.get('date', 'Today')}"
        )

        # Format summary data
        activities = summary_data.get("activities", [])
        mood = summary_data.get("mood", "Good")
        notes = summary_data.get("notes", "No special notes")

        text_content = f"""
DAILY SUMMARY - MAGGIE THOMPSON
===============================

Date: {summary_data.get("date", "Today")}
Overall Mood: {mood}

ACTIVITIES TODAY:
{chr(10).join(f"- {activity}" for activity in activities) if activities else "- No specific activities recorded"}

NOTES:
{notes}

This summary was generated by Heather, Maggie's AI assistant.

---
Heather AI Assistant
Daily Summary Report
        """.strip()

        return await self.send_email(
            ctx=ctx,
            to_emails=recipient_emails,
            subject=subject,
            text_content=text_content,
        )
