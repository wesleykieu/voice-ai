from livekit.agents import function_tool, RunContext
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger("staff_tools")


class StaffTools:
    def __init__(self, data_path="src/data"):
        self.data_path = data_path
    
    @function_tool
    async def call_staff(self, context: RunContext, reason: str):
        """Request staff assistance for a resident.
        
        Args:
            reason: Why staff is needed (e.g., "needs medication", "feeling unwell", "general assistance")
        """
        try:
            # Check if this is an emergency situation
            emergency_keywords = ["pain", "hurt", "emergency", "fall", "fell", "chest", "breath", "dizzy", "help"]
            is_emergency = any(keyword in reason.lower() for keyword in emergency_keywords)
            
            if is_emergency:
                logger.critical(f"EMERGENCY STAFF REQUEST: {reason}")
                return "I'm alerting staff immediately for urgent assistance. Help is on the way. Please stay where you are and stay calm."
            
            # Log the staff request
            logger.info(f"Staff assistance requested: {reason}")
            
            # In production, this would trigger an actual notification system
            # - Send alert to nurse station
            # - Log in care management system
            # - Track response time
            
            response = "I've notified the staff. "
            
            # Provide estimated response based on reason
            if any(word in reason.lower() for word in ["bathroom", "restroom", "toilet"]):
                response += "A caregiver will be with you shortly to assist."
            elif any(word in reason.lower() for word in ["medication", "medicine", "pill"]):
                response += "A nurse will come to help you with your medication."
            elif any(word in reason.lower() for word in ["question", "ask", "information"]):
                response += "A staff member will be here soon to answer your questions."
            else:
                response += "Someone from the care team will be with you shortly."
            
            return response
            
        except Exception as e:
            logger.error(f"Error calling staff: {str(e)}")
            # Even if there's an error, provide reassurance
            return "I'm working to contact staff for you. If this is urgent, please use your call button or ask someone nearby for immediate help."
    
    @function_tool
    async def get_staff_on_duty(self, context: RunContext):
        """Get information about which staff members are currently on duty."""
        try:
            with open(f'{self.data_path}/facility_info.json', 'r') as f:
                facility = json.load(f)
            
            # Determine current shift based on time
            current_hour = datetime.now().hour
            
            if 7 <= current_hour < 15:
                shift = "day"
            elif 15 <= current_hour < 23:
                shift = "evening"
            else:
                shift = "night"
            
            staff = facility.get("staff", {})
            current_staff = staff.get(f"{shift}_shift", [])
            
            if current_staff:
                response = f"Currently on duty ({shift} shift):\n"
                for staff_member in current_staff:
                    name = staff_member.get("name", "")
                    role = staff_member.get("role", "")
                    response += f"• {name} - {role}\n"
                
                response += "\nYou can ask any of them for help, or I can call them for you."
                return response
            else:
                return "We have nurses and caregivers available 24/7. Would you like me to call someone for you?"
                
        except FileNotFoundError:
            logger.error(f"Facility info file not found at {self.data_path}/facility_info.json")
            return "Staff members are available to help you anytime. Would you like me to call someone?"
        except Exception as e:
            logger.error(f"Error getting staff info: {str(e)}")
            return "Our care team is here 24/7. Would you like me to request assistance for you?"
    
    @function_tool
    async def emergency_alert(self, context: RunContext, situation: str):
        """Trigger an emergency alert. Use only for urgent medical situations.
        
        Args:
            situation: Description of the emergency
        """
        logger.critical(f"EMERGENCY ALERT: {situation}")
        
        # In production, this would:
        # - Trigger immediate alert to all staff
        # - Notify nurse station with room number
        # - Possibly trigger facility-wide emergency protocol
        # - Log incident with timestamp
        
        return "EMERGENCY ALERT ACTIVATED. Medical staff have been notified and are responding immediately. Stay calm, help is coming right now."
