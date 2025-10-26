# Load testing (k6)

## Local run (Windows PowerShell)
1) & .\venv_test\Scripts\Activate.ps1
2) python -m load.seed_db
3) python -m uvicorn load.server:app --reload --port 8000
4) (new window) $env:BASE_URL="http://localhost:8000"
5) k6 run load/login_and_get_schedule.js --summary-export=load/results/summary.json
