.PHONY: up down reset logs ps lint smoke wait-api wait-targets wait test bootstrap check-ssh check-ansible e2e e2e-local

up: bootstrap
	docker compose up --build

bootstrap:
	./scripts/bootstrap.sh

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

check-ssh:
	./scripts/check-ssh.sh

check-ansible:
	./scripts/check-ansible-ping.sh

e2e:
	./scripts/e2e-run-role.sh

# Hit a locally running API (uvicorn from repo root): role paths and SSH key must exist on the host.
e2e-local:
	ROLLER_ROLES_ROOT=$(CURDIR)/ansible/roles ROLLER_SSH_KEY_PATH=$(CURDIR)/ssh/id_rsa ./scripts/e2e-run-role.sh