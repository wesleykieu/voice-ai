"""
Example script to pre-populate memories for the dementia voice agent.
This demonstrates how to add sample memories for testing.
"""

from tools.memory_tool import MemoryStore

def create_sample_memories():
    """Create sample memories for testing the dementia voice agent."""
    
    # Create a memory store
    memory = MemoryStore("sample_user")
    
    # Add personal information
    memory.add_personal_info("name", "Margaret Thompson")
    memory.add_personal_info("birth_date", "March 15, 1945")
    memory.add_personal_info("hometown", "Springfield, Illinois")
    memory.add_personal_info("occupation", "Elementary school teacher")
    memory.add_personal_info("spouse_name", "Robert Thompson")
    
    # Add family members
    memory.add_family_member("Robert Thompson", "husband", "Married for 52 years, worked as an engineer, passed away in 2019")
    memory.add_family_member("Sarah", "daughter", "Lives in Chicago, works as a nurse, has two children")
    memory.add_family_member("Michael", "son", "Lives in Seattle, works in technology, married to Jennifer")
    memory.add_family_member("Emma", "granddaughter", "Sarah's daughter, 8 years old, loves to draw")
    memory.add_family_member("James", "grandson", "Sarah's son, 5 years old, loves dinosaurs")
    
    # Add life events
    memory.add_life_event("Graduated from college", "1967", "Got teaching degree from University of Illinois")
    memory.add_life_event("Married Robert", "1968", "Beautiful wedding in Springfield, honeymooned in Florida")
    memory.add_life_event("First teaching job", "1968", "Started teaching 3rd grade at Lincoln Elementary")
    memory.add_life_event("Sarah was born", "1972", "Our first child, born in June")
    memory.add_life_event("Michael was born", "1975", "Our second child, born in March")
    memory.add_life_event("Retired from teaching", "2005", "Taught for 37 years, loved every minute")
    memory.add_life_event("Robert passed away", "2019", "Peacefully at home, surrounded by family")
    memory.add_life_event("Moved to assisted living", "2022", "The Garden View facility, made new friends")
    
    # Add interests and hobbies
    memory.add_interest("Gardening", "Loves growing roses and vegetables, has a small garden plot")
    memory.add_interest("Reading", "Enjoys mystery novels and biographies, visits library weekly")
    memory.add_interest("Cooking", "Known for her apple pie and chocolate chip cookies")
    memory.add_interest("Knitting", "Makes blankets for grandchildren and donates to charity")
    memory.add_interest("Church activities", "Active in the Methodist church, sings in the choir")
    memory.add_interest("Bridge", "Plays bridge with friends every Tuesday")
    
    print("Sample memories created successfully!")
    print("\nMemory Summary:")
    print(memory.get_memory_summary())

if __name__ == "__main__":
    create_sample_memories()
