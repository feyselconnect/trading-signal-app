# Trading Signal App

This is a fullstack trading signal application with a Python backend and a React frontend.

## Project Structure

```
trading-signal-app/
│
├── backend/
│   ├── app/                # Backend source code
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example        # Backend environment variables example
│   └── ...
│
├── frontend/
│   ├── src/                # Frontend source code
│   ├── public/             # Static files (if any)
│   ├── package.json        # Frontend dependencies
│   ├── .env.example        # Frontend environment variables example
│   └── ...
│
├── .gitignore
└── README.md
```

## Setup

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
# or
source venv/bin/activate  # On Mac/Linux
pip install -r requirements.txt
cp .env.example database.env  # Fill in your secrets
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env  # If needed, fill in your API URL
npm start
```

## Usage
- Start the backend and frontend as described above.
- Access the frontend at http://localhost:3000 (or as configured).

---

**Remember:** Never commit your real `.env` files to GitHub! 