# Nursing Care Home Voice Assistant

A compassionate voice AI assistant designed for nursing care homes to help residents with daily needs, facility information, and connecting with staff. Built with LiveKit Agents and designed to provide 24/7 support to residents.

## Features

### 🏥 Facility Information
- **Dining Schedule**: Get meal times and dining room information
- **Activities**: Find out about today's or this week's scheduled activities
- **Locations**: Get directions to rooms and facilities (library, chapel, garden, etc.)
- **General Info**: Learn about visiting hours, services, and amenities

### 📅 Personal Schedule Management
- **Appointments**: Check personal appointments and schedules
- **Reminders**: Set reminders for activities or appointments
- **Daily Planning**: Get overview of the day's schedule

### 👨‍⚕️ Staff Assistance
- **Call Staff**: Request help from nurses or caregivers
- **Emergency Alerts**: Immediate response for urgent medical situations
- **Staff Directory**: Find out who's on duty

### 🛡️ Safety Features
- **Medical Disclaimer**: Never provides medical advice - always refers to staff
- **Emergency Detection**: Recognizes keywords indicating distress (pain, fall, emergency)
- **Immediate Escalation**: Prioritizes urgent requests and alerts staff

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

3. **Download Required Models**:
   ```bash
   uv run python src/agent.py download-files
   ```

4. **Run the Agent**:
   
   For terminal testing:
   ```bash
   uv run python src/agent.py console
   ```
   
   For development with frontend:
   ```bash
   uv run python src/agent.py dev
   ```

## Usage Examples

### Getting Facility Information
- "What time is lunch?"
- "When are activities today?"
- "Where is the library?"
- "Who is on duty right now?"

### Personal Schedule
- "What's on my schedule today?"
- "Remind me about my appointment at 2pm"
- "Do I have any appointments tomorrow?"

### Requesting Help
- "I need help from a nurse"
- "Can you call someone to help me?"
- "I'm not feeling well" (triggers staff call)
- "I fell!" (triggers emergency alert)

## Architecture

### Tools Structure
```
src/tools/
├── facility_tool.py    # Facility info, dining, activities, locations
├── schedule_tool.py    # Personal schedules and reminders
└── staff_tool.py       # Staff assistance and emergency alerts
```

### Data Files
```
src/data/
├── facility_info.json  # Facility details, schedules, staff
└── schedules.json      # Resident personal schedules
```

## Customization

### Update Facility Information
Edit `src/data/facility_info.json` to reflect your facility's:
- Dining hours and meal times
- Activity schedules
- Room locations and floor plans
- Staff names and shifts
- Services and amenities

### Update Activities Schedule
Modify the `activities.daily_schedule` section in `facility_info.json` to match your weekly programming.

### Add Resident Schedules
Edit `src/data/schedules.json` to add or update individual resident schedules.

### Customize Agent Personality
Modify the `instructions` in `src/agent.py` to adjust:
- Tone and language style
- Response patterns
- Safety protocols
- Escalation procedures

## Testing

Run the test suite using pytest:

```bash
uv run pytest
```

Tests include:
- Friendly greeting and assistance offering
- Medical advice refusal (always refers to staff)
- Inappropriate request handling
- Facility information retrieval
- Emergency detection and staff calling

## Safety & Compliance

### Medical Safety
- **No Medical Advice**: Agent never provides medication recommendations or medical guidance
- **Staff Referral**: All health concerns are immediately referred to nursing staff
- **Emergency Response**: Keywords like "pain", "fall", "chest", "emergency" trigger immediate alerts

### Privacy Considerations
- Resident data is stored locally
- No PHI (Protected Health Information) should be stored in plain text
- Implement encryption for production deployment
- Comply with HIPAA regulations for healthcare data

### Emergency Protocols
The agent detects emergency keywords and:
1. Logs critical alert
2. Notifies staff immediately (would integrate with nurse call system)
3. Provides reassuring response to resident
4. Documents incident timestamp

## Integration Opportunities

### Current State (MVP)
- Static facility data from JSON files
- Basic staff notification logging
- Pre-defined schedules

### Future Production Integrations
- **EHR/EMR Systems**: Real-time appointment data
- **Nurse Call Systems**: Direct integration with facility alert systems
- **Building Management**: Smart room controls, lighting, temperature
- **Calendar Systems**: Sync with facility-wide event calendars
- **Family Portal**: Share updates with family members
- **Wearables**: Integration with health monitoring devices

## Deployment

### Development
```bash
uv run python src/agent.py dev
```

### Production
```bash
uv run python src/agent.py start
```

See the [deployment guide](https://docs.livekit.io/agents/ops/deployment/) for production deployment to LiveKit Cloud or self-hosted environments.

## Frontend Options

This assistant works with any LiveKit-compatible frontend:

- **Web**: Use the [React starter](https://github.com/livekit-examples/agent-starter-react)
- **Mobile**: iOS, Android, Flutter, React Native options available
- **Telephony**: Add phone-based access for residents

See [frontend documentation](https://docs.livekit.io/agents/start/frontend/) for details.

## Contributing

When adding new features:
1. **Write tests first** (TDD approach recommended in AGENTS.md)
2. Update relevant data files
3. Document new capabilities
4. Test thoroughly with realistic scenarios

## Support

For issues or questions:
- Check LiveKit Agents documentation: https://docs.livekit.io/agents/
- Review AGENTS.md for development guidance
- Consider installing the [LiveKit Docs MCP server](https://docs.livekit.io/mcp)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Important**: This assistant is designed to support and supplement care staff, not replace them. Always ensure appropriate human oversight and intervention capabilities.
