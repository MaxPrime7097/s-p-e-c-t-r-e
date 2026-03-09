# S.P.E.C.T.R.E

S.P.E.C.T.R.E (System for Proactive Engineering and Code Technical Real-time Evaluation) is a realtime AI debugging assistant.

## Capabilities

- Screenshot analysis with Gemini (multimodal)
- Structured debugging response with:
  - `issue`, `suggestion`, `severity`, `explanation`
  - `fix_code`, `patch`, `language`
- Context memory (last 5 analyses sent back to the model)
- Realtime backend state (`/latest`) and debug timeline (`/timeline`)
- Patch application endpoint (`/apply-fix`)
- Terminal capture loop and autonomous terminal agent mode
- Realtime React panel with severity colors and voice alert on HIGH severity

## Structure

```text
spectre/
├── backend/
│   ├── main.py
│   ├── ai_analyzer.py
│   ├── suggestion_engine.py
│   ├── screen_capture.py
│   └── spectre_agent.py
└── frontend/
    └── src/
        ├── App.js
        └── components/
            └── SuggestionsPanel.js
requirements.txt
README.md
```

## Setup

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` in repo root:

```env
GEMINI_API_KEY=your_api_key_here
```

Run backend:

```bash
cd spectre/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd spectre/frontend
npx create-react-app .
npm install
export REACT_APP_API_URL=http://localhost:8000
npm start
```

## API

### `POST /analyze`
Input: multipart image. Output:

```json
{
  "issue": "Infinite React render loop",
  "suggestion": "Add dependency array to useEffect",
  "severity": "high",
  "fix_code": "useEffect(() => { fetchData(); }, []);",
  "explanation": "Without dependencies, useEffect runs on every render.",
  "patch": "- useEffect(() => {\n-  fetchData()\n- })\n+ useEffect(() => {\n+  fetchData()\n+ }, [])",
  "language": "javascript"
}
```

### `GET /latest`
Returns latest structured suggestion.

### `GET /timeline`
Returns in-memory issue history with timestamps.

### `POST /apply-fix`
Input:

```json
{
  "file_path": "/path/to/file",
  "patch": "diff style patch"
}
```

Applies patch and returns status.

## Terminal modes

Capture loop:

```bash
cd spectre/backend
python -c "from screen_capture import capture_loop; capture_loop()"
```

Autonomous agent mode:

```bash
cd spectre/backend
python spectre_agent.py
# optional auto-apply
python spectre_agent.py --auto-apply --target-file /path/to/file
```

## spectre-cli (Terminal client)

Install editable package:

```bash
pip install -e .
```

Run CLI:

```bash
python -m spectre_cli live
# or
spectre-cli live
# or
spectre live
```

Initial configuration:

```bash
spectre-cli config
```

Available commands:

- `spectre-cli live [--voice]`
- `spectre-cli status`
- `spectre-cli apply --file /path/to/file`
- `spectre-cli timeline`
- `spectre-cli config`

Config file location: `~/.spectre/config.json`.
