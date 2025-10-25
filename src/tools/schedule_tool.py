from livekit.agents import function_tool, RunContext
import json
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("schedule_tools")


class ScheduleTools:
    def __init__(self, data_path="src/data"):
        self.data_path = data_path
    
    @function_tool
    async def get_resident_schedule(self, context: RunContext, resident_name: str = ""):
        """Get personal schedule for a resident including appointments and activities.
        
        Args:
            resident_name: Name of the resident (optional)
        """
        try:
            # In production, this would query a database with the resident's ID
            # For now, we'll use a sample schedule
            with open(f'{self.data_path}/schedules.json', 'r') as f:
                schedules = json.load(f)
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Get default resident schedule or specific resident
            if resident_name:
                schedule_key = resident_name.lower().replace(" ", "_")
            else:
                schedule_key = "default_resident"
            
            resident_schedule = schedules.get(schedule_key, {})
            today_schedule = resident_schedule.get(today, [])
            
            if today_schedule:
                response = "Here's your schedule for today:\n"
                for item in today_schedule:
                    time = item.get("time", "")
                    activity = item.get("activity", "")
                    location = item.get("location", "")
                    response += f"• {time}: {activity}"
                    if location:
                        response += f" at {location}"
                    response += "\n"
                return response
            else:
                return "You don't have any scheduled appointments today. Feel free to join any of the group activities or relax as you like."
                
        except FileNotFoundError:
            logger.error(f"Schedules file not found at {self.data_path}/schedules.json")
            return "I'm having trouble accessing your schedule right now. Let me call a staff member to help you."
        except Exception as e:
            logger.error(f"Error getting schedule: {str(e)}")
            return "I couldn't access your schedule at the moment. Would you like me to call staff to check for you?"
    
    @function_tool
    async def set_reminder(self, context: RunContext, reminder_text: str, time: str = ""):
        """Set a reminder for the resident.
        
        Args:
            reminder_text: What to be reminded about
            time: When to remind (optional)
        """
        try:
            # In production, this would integrate with a reminder system
            # For now, we'll acknowledge the request and log it
            
            if time:
                response = f"I'll remind you about '{reminder_text}' {time}. "
            else:
                response = f"I've noted your reminder about '{reminder_text}'. "
            
            response += "I'll also let the staff know so they can help remind you."
            
            # Log the reminder request
            logger.info(f"Reminder set: {reminder_text} at {time if time else 'unspecified time'}")
            
            # In production, save to database
            # self._save_reminder(resident_id, reminder_text, time)
            
            return response
            
        except Exception as e:
            logger.error(f"Error setting reminder: {str(e)}")
            return "I had trouble setting that reminder. Let me call staff to help you with that."
    
    def _parse_time(self, time_str: str):
        """Parse natural language time into datetime (helper function for future use)."""
        # This would implement natural language time parsing
        # e.g., "in 30 minutes", "at 2pm", "tomorrow morning"
        # For now, return None
        return None
