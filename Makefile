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

smoke:
	./scripts/smoke-test.sh

wait-api:
	./scripts/wait-for-api.sh

wait-targets:
	./scripts/wait-for-targets.sh

wait: wait-api wait-targets