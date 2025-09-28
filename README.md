# NutriScan AI

NutriScan AI is a production-grade food data platform that ingests **Open Food Facts** data, validates and normalizes it, computes nutritional and ecological metrics like **Nutri-Score** and **Eco-Score**, and exposes both a REST API and an LLM-powered Q&A Copilot. The project is designed to practice MLOps, retrieval-augmented generation (RAG) and robust testing to deliver a system that looks and behaves like a real company product.

## Features

- **Product API**: Given a barcode it returns a clean product card including ingredients, nutrients per 100 g, Nutri-Score, Eco-Score and allergen/warning flags.
- **Compare API**: Compare two products side-by-side on nutrients and scores.
- **Scoring Service**: Compute Nutri-Score and Eco-Score with full explainability and track inputs and versions.
- **RAG Copilot**: Ask natural language questions such as "Is this vegan?" or "Compare these cereals on added sugar" and get answers with citations from your curated product facts and taxonomies.
- **Data Pipelines**: Nightly refresh of the entire Open Food Facts dump, validation with Great Expectations, normalization via official taxonomies, outlier detection, and upserts into Postgres.
- **On-demand enrichment**: If a barcode is missing from the database the service fetches it from the public OFF API, validates and scores it on the fly.
- **Monitoring & Quality**: Data drift detection with Evidently, audits table for anomalies, Prometheus metrics, and CI with unit/integration tests and RAG evaluation (Ragas).

## Architecture

The project is organised as a mono-repo. Major components are:

```
nutriscan/
  apps/api            – FastAPI service serving `/products`, `/scores`, `/compare`
  apps/rag            – FastAPI service for `/ask` (RAG copilot)
  apps/ui             – Streamlit UI (barcode lookup, compare, chat)
  pipelines/airflow   – Airflow DAGs for nightly dump refresh and taxonomy sync
  data/expectations   – Great Expectations suites for schema/quality checks
  data/taxonomies     – Cached OFF taxonomies snapshots
  models/scoring      – Nutri-Score and Eco-Score calculators with unit tests
  vectorstore         – Scripts to build FAISS index for RAG
  packages/nutriscan_utils – Reusable library (ETL helpers, schemas, OFF client)
  tests               – Unit, integration and RAG evaluation tests
  infra/docker        – Dockerfiles and configuration
  .github/workflows   – CI pipeline
  docker-compose.yml  – Compose stack (Postgres, API, RAG, UI)
  Makefile            – Developer workflows (`make dev`, `make test`, etc.)
```

See the blueprint in the project root for a complete breakdown of the desired features and acceptance criteria.

## Getting started

### Prerequisites

- Docker and Docker Compose installed locally.
- (Optional) Python 3.11 if running services outside of Docker.

### Setup

Clone the repository and start the development stack with a single command:

```bash
git clone https://github.com/ahmedtarek26/nutriscan-ai.git
cd nutriscan-ai
make dev
```

The Makefile uses `docker-compose` to spin up a Postgres database and start the API, RAG, and UI services. After the stack is healthy you can explore:

- FastAPI docs for the product API at `http://localhost:8000/docs`.
- FastAPI docs for the RAG service at `http://localhost:8001/docs`.
- Streamlit UI at `http://localhost:8501`.

To run unit tests locally:

```bash
make test
```

To build the FAISS index (after ingesting data):

```bash
make build-index
```

### Deployment

The repository includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs on every push and pull request. It checks out the code, installs dependencies and runs the test suite. You can extend this workflow to build and push container images to your registry and deploy to your hosting provider (e.g. Render or Fly.io).

### Contributing

Contributions are welcome! Feel free to open issues or pull requests with suggestions or improvements. Please refer to the blueprint in the project documentation for guidance on feature scope and architecture.

### License and Attribution

This project reuses data from [Open Food Facts](https://openfoodfacts.org/) under the **Open Database License (ODbL)**. When redistributing or running this project publicly you must credit Open Food Facts and keep the data open. See the project's LICENSE file and the [Reusing Open Food Facts Data](https://wiki.openfoodfacts.org/Reusing_Open_Food_Facts_Data) guide for more information.

---

_Note: NutriScan AI is a learning project and not intended to provide medical or dietary advice._
