.PHONY: api frontend dev test fmt

api:
	uvicorn ai_search_agent.api:app --reload --port 8000

frontend:
	cd frontend && npm run dev

dev:
	@echo "Start backend and frontend in two terminals:"
	@echo "  make api"; echo "  make frontend"

test:
	pytest -q

