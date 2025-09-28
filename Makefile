.PHONY: dev test build-index

# Start development services using Docker Compose
dev:
	@docker-compose up --build

# Run tests using pytest
 test:
	@pytest

# Build FAISS index
build-index:
	@python vectorstore/build_index.py
