.PHONY: test test_slow clean infra

APP_PATH = routing




clean:
	$(info Cleaning repository)
	find . -type d -name __pycache__ -exec rm -rfv {} +
	find . -type d -name .pytest_cache -exec rm -rfv {} +


test:
	@pytest --cache-clear --cov=${APP_PATH}

test_slow:
	@pytest --cache-clear --cov=${APP_PATH} --runslow

infra:
	docker-compose up