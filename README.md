# SQL Dashboard

A lightweight, intuitive dashboard for exploring SQLite databases with dynamic filtering and instant sharing capabilities.

## Introduction

- ⚡ **Dynamic Data Exploration** - View multiple tables simultaneously with real-time filtering across related tables
- 🔗 **URL State Management** - Your entire dashboard state (selected tables, filters) lives in the URL. Copy and paste to share results with colleagues instantly.
- 🎨 **Intuitive Interface** - Clean, simple design that gets out of your way. No learning curve required.
- 🔄 **Cross-Table Filtering** - Apply filters that automatically work across table relationships

## 🚀 Getting started

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to start exploring your databases! 🎉
