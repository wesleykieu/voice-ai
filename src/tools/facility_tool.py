from livekit.agents import function_tool, RunContext
import json
import os
import logging
from datetime import datetime, time as dt_time

logger = logging.getLogger("facility_tools")


class FacilityTools:
    def __init__(self, data_path="src/data"):
        self.data_path = data_path
    
    @function_tool
    async def get_facility_info(self, context: RunContext, query: str):
        """Get general information about the facility.
        
        Args:
            query: What information is needed (e.g., "dining hours", "activities", "locations")
        """
        try:
            with open(f'{self.data_path}/facility_info.json', 'r') as f:
                facility = json.load(f)
            
            query_lower = query.lower()
            
            # Search for relevant information
            if any(word in query_lower for word in ["meal", "dining", "eat", "food", "breakfast", "lunch", "dinner"]):
                return await self.get_dining_schedule(context)
            
            elif any(word in query_lower for word in ["activity", "activities", "event", "program"]):
                return await self.get_activities(context, "today")
            
            elif any(word in query_lower for word in ["location", "where", "find", "room", "place"]):
                # Extract location from query
                locations = facility.get("locations", {})
                for place_name in locations.keys():
                    if place_name.lower() in query_lower:
                        return await self.find_location(context, place_name)
                return "I can help you find locations in the facility. Which room or area are you looking for?"
            
            elif any(word in query_lower for word in ["staff", "nurse", "caregiver", "doctor", "who"]):
                staff_info = facility.get("staff", {})
                return f"Our care team includes nurses, caregivers, and support staff available 24/7. Would you like to know who is currently on duty?"
            
            elif any(word in query_lower for word in ["visit", "visitor", "guest", "family"]):
                visiting = facility.get("visiting_hours", {})
                return f"Visiting hours are {visiting.get('general', 'daily from 9am-8pm')}. Family members can visit anytime with prior arrangement."
            
            else:
                general = facility.get("general_info", {})
                return f"{general.get('name', 'Our facility')} is here to support you. I can help you with dining schedules, activities, finding locations, or calling staff. What would you like to know?"
                
        except FileNotFoundError:
            logger.error(f"Facility info file not found at {self.data_path}/facility_info.json")
            return "I'm having trouble accessing facility information right now. Let me call staff to help you."
        except Exception as e:
            logger.error(f"Error getting facility info: {str(e)}")
            return f"I encountered an issue: {str(e)}. How else can I help you?"
    
    @function_tool
    async def get_dining_schedule(self, context: RunContext):
        """Get today's meal times and dining information."""
        try:
            with open(f'{self.data_path}/facility_info.json', 'r') as f:
                facility = json.load(f)
            
            dining = facility.get("dining", {})
            schedule = dining.get("schedule", {})
            
            response = "Today's meal times:\n"
            response += f"Breakfast: {schedule.get('breakfast', '7:30 AM - 9:00 AM')}\n"
            response += f"Lunch: {schedule.get('lunch', '12:00 PM - 1:30 PM')}\n"
            response += f"Dinner: {schedule.get('dinner', '5:30 PM - 7:00 PM')}\n"
            
            if "location" in dining:
                response += f"\nMeals are served in the {dining['location']}."
            
            if "special_diet" in dining:
                response += f" We accommodate special dietary needs - just let the staff know."
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting dining schedule: {str(e)}")
            return "Meals are typically served at breakfast (7:30-9am), lunch (noon-1:30pm), and dinner (5:30-7pm). Let me know if you need more specific information."
    
    @function_tool
    async def get_activities(self, context: RunContext, when: str = "today"):
        """Get scheduled activities.
        
        Args:
            when: "today", "tomorrow", or "week"
        """
        try:
            with open(f'{self.data_path}/facility_info.json', 'r') as f:
                facility = json.load(f)
            
            # Get current day of week
            now = datetime.now()
            day_name = now.strftime("%A")
            
            activities = facility.get("activities", {})
            
            if when.lower() == "today":
                daily_activities = activities.get("daily_schedule", {}).get(day_name, [])
                
                if daily_activities:
                    response = f"Today's activities ({day_name}):\n"
                    for activity in daily_activities:
                        response += f"• {activity.get('time', '')}: {activity.get('name', '')} - {activity.get('location', '')}\n"
                    return response
                else:
                    return f"There are no scheduled group activities for today, but you can always enjoy the common areas, library, or garden."
            
            elif when.lower() == "week":
                response = "This week's recurring activities:\n"
                for day, day_activities in activities.get("daily_schedule", {}).items():
                    if day_activities:
                        response += f"\n{day}:\n"
                        for activity in day_activities[:2]:  # Show first 2 activities per day
                            response += f"  • {activity.get('time', '')}: {activity.get('name', '')}\n"
                return response
            
            else:
                return "I can tell you about activities today or this week. Which would you like to know?"
                
        except Exception as e:
            logger.error(f"Error getting activities: {str(e)}")
            return "We have various activities throughout the day including games, exercise, crafts, and music. Would you like me to find a staff member to give you more details?"
    
    @function_tool
    async def find_location(self, context: RunContext, place: str):
        """Help find a location in the facility.
        
        Args:
            place: The location to find
        """
        try:
            with open(f'{self.data_path}/facility_info.json', 'r') as f:
                facility = json.load(f)
            
            locations = facility.get("locations", {})
            place_lower = place.lower()
            
            # Search for the location
            for location_name, location_info in locations.items():
                if place_lower in location_name.lower():
                    directions = location_info.get("directions", "")
                    floor = location_info.get("floor", "")
                    
                    response = f"The {location_name} is located "
                    if floor:
                        response += f"on the {floor}. "
                    response += directions
                    
                    return response
            
            # If not found, provide general help
            available = ", ".join([name for name in locations.keys()])
            return f"I can help you find: {available}. Which one are you looking for?"
            
        except Exception as e:
            logger.error(f"Error finding location: {str(e)}")
            return "Let me call a staff member to help you find that location."
