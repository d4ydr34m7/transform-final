# VERAMOD

An internal enterprise tool for repository analysis.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser to the URL shown in the terminal (typically `http://localhost:5173`)

4. **Backend**: Run from `backend/` (e.g. `uvicorn main:app --reload`). Copy `backend/.env.example` to `backend/.env` and set GitHub token, S3/Bedrock/Transform/SNS as needed.

### SNS email when analysis completes

To receive an email when an analysis finishes:

1. **AWS Console** → SNS → Topics → Create topic (Standard) → note the **Topic ARN**.
2. **Create subscription**: Protocol **Email**, Endpoint = your email → Create.
3. **Confirm**: Open the email from AWS and click the confirmation link (subscription must show **Confirmed**).
4. **Backend `.env`**: Set `SEND_COMPLETION_NOTIFICATION=true` and `SNS_TOPIC_ARN=arn:aws:sns:REGION:ACCOUNT:TOPIC_NAME`.
5. Restart the backend. IAM credentials used by the backend need `sns:Publish` on that topic.

### Transform output

When Transform (atx) runs, the backend saves **transform.log** (stdout/stderr) and copies the **Transform output directory** (e.g. `Documentation/`) from the cloned repo into the analysis artifacts (S3 or local). That directory is then listed in the UI and included in the download. The output dir name is configurable via `TRANSFORM_OUTPUT_DIR` (default `Documentation`). The UI shows analysis files by analysis ID; clicking a different analysis in History now correctly loads that analysis’s files and clears the previous viewer.

## Project Structure

- `src/components/` - Shared components (Navbar)
- `src/pages/` - Page components (RepoSelection, AnalysisResults)
- `src/App.tsx` - Main app component with routing
- `src/main.tsx` - Entry point

## Features

- **Page 1 - Repo Selection**: Centered card with repository input and "Run Analysis" button
- **Page 2 - Analysis Results**: Three-pane layout with file explorer, document viewer, and chat interface

All styling follows the enterprise theme with no external UI libraries, using plain CSS only.
