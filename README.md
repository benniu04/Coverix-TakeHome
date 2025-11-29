# Insurance Onboarding Chatbot

A conversational chatbot for insurance onboarding that collects user information through a guided flow. Built with FastAPI (Python) and React (TypeScript).

## Features

- 🤖 **AI-Powered Conversations**: Uses OpenAI GPT-4o-mini for natural language understanding
- 🚗 **Vehicle Validation**: Validates VINs and vehicle makes against NHTSA API
- 💾 **Real-time Database Storage**: All conversations are stored in SQLite for review
- 🎯 **State Machine Flow**: Guided conversation that collects information in order
- 😌 **Frustration Detection**: Detects upset users and provides calming quotes via ZenQuotes API
- 🎨 **Modern Dark UI**: Beautiful, responsive chat interface

## Flow

The chatbot collects information in this order:

1. **ZIP Code** - 5-digit US zip code
2. **Full Name** - User's complete name
3. **Email Address** - Valid email for contact
4. **Vehicle Information** (can add multiple):
   - VIN (17 characters) OR Year/Make/Body Type
   - Vehicle Use (Commuting, Commercial, Farming, Business)
   - Blind Spot Warning (Yes/No)
   - If Commuting: Days per week, One-way miles
   - If Commercial/Farming/Business: Annual mileage
5. **License Type** - Foreign, Personal, or Commercial
6. **License Status** - Valid or Suspended (if not Foreign)

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **SQLite** - Lightweight database
- **OpenAI** - GPT-4o-mini for conversation generation
- **httpx** - Async HTTP client for API calls

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **CSS3** - Custom styling with CSS variables

## Prerequisites

- Python 3.9+
- Node.js 18+
- OpenAI API key

## Setup Instructions

### 1. Backend Setup

**IMPORTANT:** You need an OpenAI API key to run the backend!

```bash
# Navigate to backend
cd backend

# Create .env file with your OpenAI API key (REQUIRED!)
echo "OPENAI_API_KEY='sk-your_actual_api_key_here'" > .env
# Replace sk-your_actual_api_key_here with your real OpenAI API key

# Option 2: Manual setup
python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python main.py
```

The backend will start at `http://localhost:8000`

**Common Issues:**
- ❌ `ModuleNotFoundError: No module named 'fastapi'` → You're using system Python instead of venv. Use `./venv/bin/python main.py`
- ❌ `OPENAI_API_KEY not found` → Create the `.env` file with your API key first

### 2. Frontend Setup

Open a new terminal:

```bash
# Navigate to frontend
cd frontend

# Option 2: Manual setup
npm install
npm run dev
```

The frontend will start at `http://localhost:5173`

### 3. Open the App

Navigate to `http://localhost:5173` in your browser to start chatting!

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/conversation/start` | Start a new conversation |
| POST | `/api/chat` | Send a message |
| GET | `/api/conversation/{session_id}` | Get conversation details |
| GET | `/api/conversations` | List all conversations |

## Database Schema

The SQLite database (`chatbot.db`) contains:

- **conversations**: User information and conversation state
- **messages**: Chat transcript with timestamps
- **vehicles**: Vehicle details for each conversation

You can inspect the database using any SQLite viewer or:

```bash
sqlite3 backend/chatbot.db
.tables
SELECT * FROM conversations;
SELECT * FROM messages;
SELECT * FROM vehicles;
```

## Project Structure

```
Coverix-TakeHome/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── database.py             # Database configuration
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   ├── conversation_engine.py  # Flow logic & state management
│   ├── requirements.txt        # Python dependencies
│   └── services/
│       ├── openai_service.py   # OpenAI integration
│       ├── nhtsa.py            # Vehicle validation
│       └── zenquotes.py        # Calming quotes API
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Main app component
│   │   ├── components/         # React components
│   │   ├── hooks/              # Custom hooks
│   │   └── types/              # TypeScript types
│   └── package.json
└── README.md
```

## Environment Variables

### Backend (.env)
```
OPENAI_API_KEY=sk-...  # Your OpenAI API key
```

## Testing the Chatbot

1. Start a conversation - the bot will greet you
2. Enter your ZIP code (e.g., "90210")
3. Provide your name
4. Enter your email
5. Choose VIN or manual vehicle entry
6. If VIN: enter a valid 17-character VIN (e.g., "1HGCM82633A123456")
7. Answer vehicle questions
8. Add more vehicles or continue to license
9. Complete the onboarding!

### Testing Frustration Detection

Try saying things like:
- "This is frustrating"
- "I want to speak to a human"
- "This doesn't work"

The bot will respond with a calming quote from ZenQuotes.

## Troubleshooting

**Backend won't start?**
- Check that your OpenAI API key is valid
- Make sure port 8000 is free
- Check Python version (3.9+ required)

**Frontend won't connect?**
- Ensure backend is running on port 8000
- Check CORS settings if using different ports

**VIN validation fails?**
- NHTSA API may be slow - wait a moment
- Ensure VIN is exactly 17 characters
- Some VINs may not be in the database

