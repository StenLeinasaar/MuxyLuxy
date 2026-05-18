.PHONY: up down reset logs ps lint smoke wait-api wait-targets wait test

up:
	docker compose up --build

down:
	docker compose down

reset:
	docker compose down -v --remove-orphans

logs:
	docker compose logs -f

ps:
	docker compose ps

lint:
	./scripts/lint.sh

smoke:
	./scripts/smoke-test.sh

wait-api:
	./scripts/wait-for-api.sh

wait-targets:
	./scripts/wait-for-targets.sh

wait: wait-api wait-targets

test:
	./scripts/test.sh