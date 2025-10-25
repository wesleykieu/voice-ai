from livekit.agents import function_tool, RunContext
import json
import os
import logging

logger = logging.getLogger("memory_tools")

class MemoryTools:
    def __init__(self, data_path="src/data"):
        self.data_path = data_path
    
    @function_tool
    async def search_memories(self, context: RunContext, topic: str):
        """Search through Maggie's personal memories about a specific topic.
        
        Args:
            topic: The topic to search for (e.g., "teaching", "Robert", "childhood", "wedding")
        """
        
        try:
            with open(f'{self.data_path}/memories.json', 'r') as f:
                memories = json.load(f)
            
            relevant_memories = []
            
            # Search through all memory categories
            for category, memory_list in memories.items():
                if category == 'person':
                    continue
                    
                if isinstance(memory_list, list):
                    for memory in memory_list:
                        if isinstance(memory, dict):
                            # Search in title and description
                            searchable_text = f"{memory.get('title', '')} {memory.get('description', '')}".lower()
                            if topic.lower() in searchable_text:
                                age_info = f" when I was {memory['age']}" if 'age' in memory else ""
                                relevant_memories.append(
                                    f"{memory.get('title', 'A memory')}{age_info}: {memory.get('description', '')[:250]}"
                                )
            
            if relevant_memories:
                return f"I remember {len(relevant_memories)} things about {topic}. " + " ".join(relevant_memories[:2])
            else:
                return f"I don't recall specific memories about {topic} right now, but I'm happy to talk about my life."
                
        except FileNotFoundError:
            logger.error(f"Memories file not found at {self.data_path}/memories.json")
            return "I'm having trouble accessing my memories right now."
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return f"I had trouble remembering: {str(e)}"
    
    @function_tool
    async def search_memories_by_age(self, context: RunContext, age: str):
        """Search for memories from when Maggie was a specific age.
        
        Args:
            age: The age to search for (e.g., "25", "50", "70")
        """
        
        try:
            target_age = int(age)
            
            with open(f'{self.data_path}/memories.json', 'r') as f:
                memories = json.load(f)
            
            found_memories = []
            
            for category, memory_list in memories.items():
                if category == 'person':
                    continue
                    
                if isinstance(memory_list, list):
                    for memory in memory_list:
                        if isinstance(memory, dict) and memory.get('age') == target_age:
                            found_memories.append(
                                f"{memory.get('title', 'A memory')}: {memory.get('description', '')[:200]}"
                            )
            
            if found_memories:
                return f"When I was {age}, " + " Also, ".join(found_memories[:2])
            else:
                return f"I don't have specific memories written down from age {age}, but those were good years."
                
        except ValueError:
            return "Please tell me a specific age number."
        except Exception as e:
            logger.error(f"Error searching by age: {str(e)}")
            return f"I had trouble remembering: {str(e)}"
    
    @function_tool
    async def get_personal_info(self, context: RunContext):
        """Get basic personal information about Maggie."""
        
        try:
            with open(f'{self.data_path}/memories.json', 'r') as f:
                memories = json.load(f)
            
            person = memories.get('person', {})
            
            info = f"My name is {person.get('name', 'Margaret Rose Thompson')}, but everyone calls me {person.get('nickname', 'Maggie')}. "
            info += f"I was born on {person.get('birth_date', 'April 15, 1932')} in {person.get('birth_place', 'Brooklyn, New York')}. "
            info += f"I was an elementary school teacher for {person.get('years_teaching', 38)} wonderful years. "
            info += f"I love {person.get('favorite_flower', 'yellow roses')} and {', '.join(person.get('hobbies', ['reading']))}."
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting personal info: {str(e)}")
            return "I'm Maggie, and I was a teacher for many years. I love reading and my family."
    
    @function_tool
    async def get_family_info(self, context: RunContext):
        """Get information about Maggie's family members - children, grandchildren, spouse."""
        
        try:
            with open(f'{self.data_path}/memories.json', 'r') as f:
                memories = json.load(f)
            
            family_info = []
            
            # Get spouse info
            if 'young_adult_memories' in memories:
                for memory in memories['young_adult_memories']:
                    if 'Robert' in memory.get('title', '') and 'Meeting' in memory.get('title', ''):
                        family_info.append("I was married to Robert James Thompson for 52 wonderful years until he passed in 2007.")
                        break
            
            # Get children
            children = []
            if 'motherhood_memories' in memories:
                for memory in memories['motherhood_memories']:
                    if 'child' in memory and 'Child' in memory.get('title', ''):
                        child_name = memory['child']
                        if child_name not in children:
                            children.append(child_name)
            
            if children:
                family_info.append(f"I have three children: {', '.join(children)}.")
            
            # Count grandchildren
            grandchildren = set()
            if 'family_milestones' in memories:
                for memory in memories['family_milestones']:
                    if 'grandchild' in memory:
                        grandchildren.add(memory['grandchild'])
            
            if grandchildren:
                family_info.append(f"I'm blessed with {len(grandchildren)} grandchildren.")
            
            # Great-grandchildren
            if 'family_milestones' in memories:
                for memory in memories['family_milestones']:
                    if 'Great-Grandchild' in memory.get('title', ''):
                        family_info.append("I even have great-grandchildren now!")
                        break
            
            if family_info:
                return " ".join(family_info)
            else:
                return "I have a wonderful family - children, grandchildren, and great-grandchildren who mean the world to me."
                
        except Exception as e:
            logger.error(f"Error getting family info: {str(e)}")
            return "I have a wonderful family that I love very much."
    
    @function_tool
    async def get_teaching_memories(self, context: RunContext):
        """Get memories about Maggie's 38-year teaching career."""
        
        try:
            with open(f'{self.data_path}/memories.json', 'r') as f:
                memories = json.load(f)
            
            teaching_memories = memories.get('teaching_memories', [])
            
            if teaching_memories:
                # Get 2 random teaching stories
                stories = [
                    f"{m.get('title')}: {m.get('description', '')[:200]}"
                    for m in teaching_memories[:2]
                ]
                return f"I taught for 38 years. " + " Another memory: ".join(stories)
            else:
                return "I was an elementary school teacher for 38 years. Teaching reading to children was my passion."
                
        except Exception as e:
            logger.error(f"Error getting teaching memories: {str(e)}")
            return "I was a teacher for 38 years and I loved every minute of it."
    
    @function_tool
    async def get_childhood_memories(self, context: RunContext):
        """Get memories from Maggie's childhood in Brooklyn."""
        
        try:
            with open(f'{self.data_path}/memories.json', 'r') as f:
                memories = json.load(f)
            
            childhood = memories.get('childhood_memories', [])
            
            if childhood:
                stories = [
                    f"{m.get('title')}: {m.get('description', '')[:200]}"
                    for m in childhood[:2]
                ]
                return "Growing up in Brooklyn was special. " + " ".join(stories)
            else:
                return "I grew up in Brooklyn during the Depression. Those were hard times but we had love."
                
        except Exception as e:
            logger.error(f"Error getting childhood memories: {str(e)}")
            return "I grew up in Brooklyn during the Great Depression."
    
    @function_tool
    async def get_wisdom(self, context: RunContext, topic: str = ""):
        """Get Maggie's wisdom and reflections on life topics.
        
        Args:
            topic: Optional topic like "love", "motherhood", "aging", "teaching", "loss"
        """
        
        try:
            with open(f'{self.data_path}/memories.json', 'r') as f:
                memories = json.load(f)
            
            wisdom = memories.get('wisdom_and_reflections', [])
            
            if topic:
                # Search for specific topic
                for reflection in wisdom:
                    if topic.lower() in reflection.get('title', '').lower():
                        return f"About {reflection.get('title')}: {reflection.get('description', '')}"
            
            # Return first wisdom if no topic specified
            if wisdom:
                return wisdom[0].get('description', 'Every day is a gift.')
            else:
                return "I've learned that love and family are what matter most in life."
                
        except Exception as e:
            logger.error(f"Error getting wisdom: {str(e)}")
            return "The most important things in life are love, family, and kindness."
    
    @function_tool
    async def get_life_story_summary(self, context: RunContext):
        """Get a brief summary of Maggie's life story."""
        
        try:
            with open(f'{self.data_path}/memories.json', 'r') as f:
                memories = json.load(f)
            
            person = memories.get('person', {})
            
            summary = f"I'm {person.get('name', 'Margaret Rose Thompson')}, born in {person.get('birth_place', 'Brooklyn')} in 1932. "
            summary += f"I grew up during the Depression, became a teacher, and taught for {person.get('years_teaching', 38)} years. "
            summary += "I married my wonderful husband Robert and we had three children together. "
            summary += "Now at 92, I have grandchildren and great-grandchildren. "
            summary += "I've lived a full life filled with love, teaching, and family."
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting life story: {str(e)}")
            return "I've lived 92 years full of love, teaching, and family. It's been a beautiful life."