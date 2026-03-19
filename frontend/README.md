# QuizSensei - Frontend Application

This directory contains the **Next.js (App Router)** frontend for QuizSensei.

## Tech Stack
- **Framework:** Next.js 15+ (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS v4
- **State Management:** Zustand
- **Icons:** Heroicons

## Features
- **3-Panel Notebook View:** Designed similarly to NotebookLM, split into.
  1. **SourceList (Left Panel):** File upload and document management.
  2. **SourceViewer (Center Panel):** Reading extracted text and Gatekeeper (Agent 1) analysis.
  3. **QuizGenerator (Right Panel):** Requesting and viewing generated exams from Agent 2/3.

## Environment Variables
The frontend communicates directly with the FastAPI backend. By default, API calls point to `http://localhost:8000`. 
Ensure your backend is running before using the UI.

## Local Development
```bash
npm install
npm run dev
```

## Docker Build
This frontend is configured with `output: "standalone"` in `next.config.ts`.
It is automatically built and served via the root `docker-compose.yml` file.
