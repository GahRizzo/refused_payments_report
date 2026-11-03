.PHONY: help install run test test-unit test-integration coverage lint format format-check check build

.DEFAULT_GOAL := help

UV := $(shell command -v uv 2>/dev/null || echo $(HOME)/.local/bin/uv)

help:
	@echo "Comandos disponíveis:"
	@echo "  make setup            - Instala o uv (se necessário) e sincroniza as dependências"
	@echo "  make setup-uv         - Instala o uv caso não esteja disponível"
	@echo "  make install          - Instala as dependências"
	@echo "  make run              - Executa o pipeline"
	@echo "  make test             - Executa todos os testes"
	@echo "  make test-unit        - Executa testes unitários"
	@echo "  make test-integration - Executa testes de integração"
	@echo "  make coverage         - Executa testes com cobertura"
	@echo "  make lint             - Verifica o código com Ruff"
	@echo "  make format           - Formata o código com Black"
	@echo "  make format-check     - Verifica a formatação"
	@echo "  make check            - Executa lint, formatação e testes"
	@echo "  make build            - Gera os pacotes de distribuição"

setup-uv:
	@if command -v uv >/dev/null 2>&1 || [ -x "$(HOME)/.local/bin/uv" ]; then \
		echo "uv já está instalado."; \
	else \
		echo "Instalando uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	fi

setup: setup-uv install

install:
	$(UV) sync --locked

run:
	$(UV) run refused-payments-report

test:
	$(UV) run pytest tests/ -v

test-unit:
	$(UV) run pytest tests/unit/ -v

test-integration:
	$(UV) run pytest tests/integration/ -v

coverage:
	$(UV) run pytest tests/ --cov=refused_payments_report --cov-branch --cov-report=term-missing

lint:
	$(UV) run ruff check src/ tests/

format:
	$(UV) run black src/ tests/

format-check:
	$(UV) run black --check src/ tests/

check: lint format-check coverage

build:
	$(UV) build