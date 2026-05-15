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