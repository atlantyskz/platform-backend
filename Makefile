# Определяем переменные для окружений
ENVIRONMENT ?= dev

# Команды для dev окружения
run-dev:
	docker compose -f docker-compose.dev.yml up

build-dev:
	docker compose -f docker-compose.dev.yml up --build

migrate-dev:
	docker compose -f docker-compose.dev.yml exec web alembic upgrade head

migrate-create-dev:
	docker compose -f docker-compose.dev.yml exec web alembic revision --autogenerate -m "$(name)"

# Команды для prod окружения
run-prod:
	docker compose -f docker-compose.prod.yml up

build-prod:
	docker compose -f docker-compose.prod.yml up --build

migrate-prod:
	docker compose -f docker-compose.prod.yml exec web alembic upgrade head

migrate-create-prod:
	docker compose -f docker-compose.prod.yml exec web alembic revision --autogenerate -m "$(name)"

# Вы можете добавить команды для общего управления
run:
	if [ "$(ENVIRONMENT)" = "prod" ]; then \
		make run-prod; \
	else \
		make run-dev; \
	fi

build:
	if [ "$(ENVIRONMENT)" = "prod" ]; then \
		make build-prod; \
	else \
		make build-dev; \
	fi

migrate:
	if [ "$(ENVIRONMENT)" = "prod" ]; then \
		make migrate-prod; \
	else \
		make migrate-dev; \
	fi

migrate-create:
	if [ "$(ENVIRONMENT)" = "prod" ]; then \
		make migrate-create-prod; \
	else \
		make migrate-create-dev; \
	fi
