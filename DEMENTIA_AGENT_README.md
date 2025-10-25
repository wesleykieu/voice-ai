# Dementia Voice Agent

A compassionate voice AI agent designed to help people with dementia maintain their personal history and have meaningful conversations. The agent can store, recall, and discuss personal memories, family information, life events, and interests.

## Features

### Memory Management
- **Personal Information**: Store name, birth date, hometown, occupation, etc.
- **Family Members**: Remember family relationships and details
- **Life Events**: Record important moments and milestones
- **Interests & Hobbies**: Track personal passions and activities
- **Memory Search**: Find specific memories by topic
- **Memory Summary**: Get an overview of all stored information

### Voice Interaction
- **Compassionate Tone**: Calm, patient, and reassuring communication
- **Memory-Aware Conversations**: References stored memories during discussions
- **Gentle Questioning**: Helps users recall and share their stories
- **Supportive Responses**: Encouraging when memory is challenging

## Setup

1. **Install Dependencies**:
   ```bash
   cd voice-ai
   uv sync
   ```

2. **Set Environment Variables**:
   Add your API keys to `.env.local`:
   ```
   LIVEKIT_API_KEY="your_livekit_key"
   LIVEKIT_API_SECRET="your_livekit_secret"
   LIVEKIT_URL="your_livekit_url"
   GROQ_API_KEY="your_groq_key"
   ```

3. **Run the Agent**:
   ```bash
   uv run python src/agent.py dev
   ```

## Usage Examples

### Storing Memories
Users can tell the agent about their life, and it will automatically store the information:

- "My name is Margaret Thompson"
- "I was born on March 15, 1945"
- "I have a daughter named Sarah who lives in Chicago"
- "I used to be a teacher and I retired in 2005"
- "I love gardening and knitting"

### Recalling Memories
The agent can search and recall stored information:

- "Tell me about my family"
- "What did I do for work?"
- "What are my hobbies?"
- "Tell me about my grandchildren"

### Conversational Memory
The agent uses stored memories to have meaningful conversations:

- "How are you today, Margaret? I remember you mentioned you were working on a new knitting project."
- "You told me your daughter Sarah is a nurse. How is she doing?"

## Memory Tools

The agent has access to these tools:

1. **store_personal_info**: Store basic personal information
2. **add_life_event**: Record life events with dates and details
3. **add_family_member**: Add family member information
4. **add_interest**: Track hobbies and interests
5. **get_memory_summary**: Get overview of all memories
6. **search_memories**: Find specific memories by topic

## Pre-populating Memories

You can pre-populate memories using the example script:

```bash
uv run python src/example_memories.py
```

This creates sample memories for testing the system.

## Memory Storage

Memories are stored in JSON files:
- `memories_default.json` - Default user's memories
- `memories_[user_id].json` - Specific user's memories

## Customization

### Adding New Memory Types
Edit `src/tools/memory_tool.py` to add new categories of memories.

### Modifying Agent Personality
Update the instructions in `src/agent.py` to change the agent's tone or behavior.

### Adding New Tools
Create new function tools in the Assistant class for additional functionality.

## Privacy & Security

- Memories are stored locally in JSON files
- No data is sent to external services except for the LLM processing
- Consider encryption for sensitive personal information
- Implement user authentication for multi-user scenarios

## Future Enhancements

- **Photo Integration**: Store and discuss family photos
- **Voice Memos**: Record and play back personal voice messages
- **Memory Triggers**: Remind users of important dates and events
- **Family Sharing**: Allow family members to add memories
- **Memory Games**: Interactive activities to help with memory
- **Medical Integration**: Connect with healthcare providers

## Support

This agent is designed to be a supportive companion for people with dementia and their families. It should never replace professional medical care or human interaction, but rather supplement and enhance the care experience.

## License

This project is part of the LiveKit Agents ecosystem and follows the same licensing terms.
