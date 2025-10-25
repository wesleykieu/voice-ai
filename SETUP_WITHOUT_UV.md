# Setup Without UV - Using Standard Python

You can run this nursing care home assistant using standard Python and pip instead of uv.

## Prerequisites

- Python 3.9 or higher
- pip (comes with Python)

Check your Python version:
```bash
python3 --version
```

## Setup Instructions

### 1. Create a Virtual Environment (Recommended)

```bash
cd /Users/dhananjaysurti/personal/voice-ai

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# OR
.\venv\Scripts\activate  # On Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Create a `.env.local` file in the project root:

```bash
# Copy the example file
cp .env.example .env.local

# Edit it with your API keys
nano .env.local  # or use any text editor
```

Add your API keys:
```
LIVEKIT_URL="your_livekit_url"
LIVEKIT_API_KEY="your_livekit_key"
LIVEKIT_API_SECRET="your_livekit_secret"
GROQ_API_KEY="your_groq_key"
```

### 4. Download Required Models

```bash
python3 src/agent.py download-files
```

## Running the Agent

### Console Mode (Test in Terminal)

```bash
python3 src/agent.py console
```

This lets you talk to the agent directly in your terminal.

### Development Mode (For Frontend Integration)

```bash
python3 src/agent.py dev
```

### Production Mode

```bash
python3 src/agent.py start
```

## Running Tests

```bash
# Make sure you're in the virtual environment
python3 -m pytest

# Or with more verbose output
python3 -m pytest -v
```

## Testing Individual Components

You can test the tools directly:

```bash
python3 -c "
import sys
sys.path.insert(0, 'src')
from tools.facility_tool import FacilityTools
import asyncio

async def test():
    tools = FacilityTools()
    result = await tools.get_dining_schedule(None)
    print(result)

asyncio.run(test())
"
```

## Common Commands Cheat Sheet

| Task | Command |
|------|---------|
| Activate venv | `source venv/bin/activate` |
| Install deps | `pip install -r requirements.txt` |
| Download models | `python3 src/agent.py download-files` |
| Test in console | `python3 src/agent.py console` |
| Run for frontend | `python3 src/agent.py dev` |
| Run tests | `python3 -m pytest` |
| Deactivate venv | `deactivate` |

## Troubleshooting

### Import Errors

If you get import errors, make sure:
1. Virtual environment is activated
2. Dependencies are installed: `pip install -r requirements.txt`
3. You're in the project root directory

### Missing Modules

```bash
# Install a specific missing package
pip install <package-name>
```

### Python Version Issues

If you have multiple Python versions:
```bash
# Use a specific version
python3.11 -m venv venv
# or
python3.10 -m venv venv
```

### Torch Installation Issues

If torch installation fails, try:
```bash
# Install torch separately first
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Then install the rest
pip install -r requirements.txt
```

## Differences from UV

| UV Command | Standard Python Equivalent |
|------------|---------------------------|
| `uv sync` | `pip install -r requirements.txt` |
| `uv run python ...` | `python3 ...` (with venv activated) |
| `uv run pytest` | `python3 -m pytest` |
| `uv add <package>` | `pip install <package>` then update requirements.txt |

## Development Workflow

1. **Activate virtual environment** every time you work on the project:
   ```bash
   source venv/bin/activate
   ```

2. **Make changes** to your code

3. **Test changes**:
   ```bash
   python3 -m pytest
   # or
   python3 src/agent.py console
   ```

4. **Deactivate** when done:
   ```bash
   deactivate
   ```

## Adding New Dependencies

If you need to add a new package:

```bash
# Install it
pip install <package-name>

# Update requirements.txt
pip freeze > requirements.txt
```

Or manually add to `requirements.txt` and run:
```bash
pip install -r requirements.txt
```

## Virtual Environment Benefits

Using a virtual environment:
- ✅ Keeps project dependencies isolated
- ✅ Prevents conflicts with system Python packages
- ✅ Makes it easy to reproduce the environment
- ✅ Allows different Python versions per project

---

**You're all set!** No need for `uv` - standard Python tools work perfectly fine.
