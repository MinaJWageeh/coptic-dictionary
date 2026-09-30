# Arabic to Coptic Translator

Hybrid translation system for Arabic to Coptic. It combines a sourced dictionary, Arabic senses, Coptic dialects, parallel examples, grammar rules, pgvector retrieval, and human review. New sentence translations are saved as `draft` candidates and must be approved by a reviewer before they are treated as reviewed output.

## What Is Implemented

- **Backend:** FastAPI, SQLAlchemy, Alembic, JWT auth, role-based access for `user`, `reviewer`, and `admin`.
- **Database:** PostgreSQL schema with `pgvector` support for parallel segments, Arabic senses, and grammar rules.
- **Translation pipeline:** word lookup and sentence pipeline with normalization, tokenization, dictionary coverage, retrieval references, grammar notes, confidence scoring, and draft candidate persistence.
- **RAG layer:** deterministic local embeddings for development plus pgvector-compatible columns and retrieval service.
- **Admin web panel:** Next.js + TypeScript, React Query, Zod forms, protected routes, CRUD-oriented management screens, request dashboard, and review queue.
- **Audit trail:** administrative create/update/delete actions are recorded in `audit_logs` and exposed in the admin panel.
- **Review feedback loop:** reviewer-approved or corrected sentence candidates are stored back as approved `parallel_segments` for future retrieval.
- **User web translator:** protected `/translate` screen showing translation/candidate, literal breakdown, references, confidence, unknown words, and review status.
- **Mobile app:** Expo React Native starter with login, dialect selection, translation, and evidence display.
- **Tests:** pytest coverage for auth, translation service/API, retrieval, low-confidence cases, unknown words, and approved existing translations.
- **Docker:** `docker-compose.yml` starts PostgreSQL/pgvector, Redis, backend, and web.

## Project Structure

```text
Coptic_Dic/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routers: auth, public, admin, review, retrieval
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # translation, retrieval, dictionary, review, admin
│   │   ├── pipeline/     # modular pipeline primitives
│   │   └── seed/         # idempotent development seed data
│   ├── alembic/
│   └── tests/
├── web/
│   ├── src/app/          # Next.js routes: login, dashboard, translate, resources, review
│   ├── src/components/
│   └── src/lib/
├── mobile/
│   ├── app/              # Expo Router screens
│   ├── src/              # API, storage, shared mobile components
│   └── __tests__/
├── docker-compose.yml
└── ARCHITECTURE.md
```

## Run With Docker

Create an optional local env file from the example:

```bash
copy .env.example .env
```

On macOS/Linux use:

```bash
cp .env.example .env
```

Start the whole stack with one command:

```bash
docker compose up --build
```

Services:

- Backend API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- Web app/admin panel: `http://localhost:3000`
- PostgreSQL with pgvector: `localhost:5432`
- Redis: `localhost:6379`

The backend container waits for PostgreSQL and Redis health checks, runs Alembic migrations, seeds sample data, and then starts FastAPI. PostgreSQL uses the `pgvector/pgvector:pg16` image so the `vector` extension is available for the RAG fields.

Useful Docker commands:

```bash
# Start in the foreground
docker compose up --build

# Start in the background
docker compose up --build -d

# Show logs
docker compose logs -f backend
docker compose logs -f web

# Stop containers but keep database volumes
docker compose down

# Stop and delete database/cache volumes
docker compose down -v
```

Run migrations manually:

```bash
docker compose exec backend alembic upgrade head
```

Seed the database manually:

```bash
docker compose exec backend python -m app.seed.run
```

Open a PostgreSQL shell:

```bash
docker compose exec postgres psql -U coptic -d coptic_dic
```

Run tests locally as shown in the backend, web, and mobile sections below. The Docker images are production-oriented and intentionally avoid copying test folders into runtime containers.

Development seed users:

- `admin@example.com` / `ChangeMe123!`
- `reviewer@example.com` / `ChangeMe123!`
- `user@example.com` / `ChangeMe123!`

Seed Coptic examples are for development smoke testing only. Replace them with scholarly source-backed data before production.

### Docker Environment Variables

Root `.env.example` contains the compose-level variables:

```text
POSTGRES_DB=coptic_dic
POSTGRES_USER=coptic
POSTGRES_PASSWORD=coptic_pass
POSTGRES_PORT=5432
REDIS_PORT=6379
BACKEND_PORT=8000
WEB_PORT=3000
JWT_SECRET=change-me-in-production
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8081
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
SEED_ON_STARTUP=true
EMBEDDING_ENABLED=true
```

For production, change `JWT_SECRET`, database credentials, and CORS origins. Set `SEED_ON_STARTUP=false` if you want migrations to run automatically but seed data to be inserted only by the manual seed command. `NEXT_PUBLIC_API_BASE_URL` is embedded into the browser bundle at web image build time, so rebuild the web image after changing it:

```bash
docker compose build web --no-cache
docker compose up -d web
```

## Local Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
python -m app.seed.run
uvicorn app.main:app --reload --port 8000
```

Run tests:

```bash
cd backend
python -m pytest tests -q
```

## Local Web

```bash
cd web
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` in `web/.env.local` if needed.

Run web tests:

```bash
cd web
npm run test
```

## Local Mobile

```bash
cd mobile
npm install
npx expo start
```

For a physical device, set:

```bash
EXPO_PUBLIC_API_BASE_URL=http://YOUR-LAN-IP:8000
```

Run mobile tests:

```bash
cd mobile
npm run test -- --runInBand
```

Run all local test suites:

```bash
cd backend && python -m pytest tests -q
cd ../web && npm run test
cd ../mobile && npm run test -- --runInBand
```

## Common Docker Errors

- **Port already in use:** change `POSTGRES_PORT`, `REDIS_PORT`, `BACKEND_PORT`, or `WEB_PORT` in `.env`, then run `docker compose up --build` again.
- **Web cannot reach backend:** confirm `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` for browser access, then rebuild the web image because public Next.js variables are baked at build time.
- **Backend cannot connect to DB:** verify the compose database URL uses host `postgres`, not `localhost`, inside containers.
- **Missing pgvector extension:** use the configured `pgvector/pgvector:pg16` image and run `docker compose down -v` if an older non-pgvector volume/image was used previously.
- **Migrations fail on an old database:** inspect the error with `docker compose logs backend`; for disposable dev data, reset with `docker compose down -v` and then `docker compose up --build`.
- **Seed data duplicates:** the seed script is idempotent; if data looks stale, reset volumes with `docker compose down -v`.
- **Slow backend image build:** `sentence-transformers` pulls ML dependencies. Keep Docker layer cache intact when possible and avoid `--no-cache` unless env/build artifacts need a clean rebuild.

## Core API

Public/user:

- `POST /auth/login`
- `POST /translate`
- `GET /dictionary/search?q=`
- `GET /dictionary/{id}`
- `GET /examples/search?q=`
- `GET /dialects`

Retrieval:

- `POST /retrieval/similar-segments`

Admin:

- `POST|GET /admin/dictionary`
- `PUT|DELETE /admin/dictionary/{id}`
- `GET|POST /admin/senses`
- `PUT|DELETE /admin/senses/{id}`
- `GET|POST /admin/mappings`
- `PUT|DELETE /admin/mappings/{id}`
- `GET|POST /admin/corpus-texts`
- `PUT|DELETE /admin/corpus-texts/{id}`
- `GET|POST /admin/parallel-segments`
- `PUT|DELETE /admin/parallel-segments/{id}`
- `GET|POST /admin/grammar-rules`
- `PUT|DELETE /admin/grammar-rules/{id}`
- `GET|POST /admin/sources`
- `PUT|DELETE /admin/sources/{id}`
- `GET|POST /admin/users`
- `PUT|DELETE /admin/users/{id}`
- `GET /admin/audit-logs`
- `GET /admin/translation-requests`
- `GET /admin/translation-candidates`

Reviewer:

- `GET /review/translation-requests`
- `GET /review/translation-candidates`
- `POST /review/translation/{id}/approve`
- `POST /review/translation/{id}/reject`
- `POST /review/translation/{id}/correct`

## Reliability Rules

- Single Arabic words are translated only through dictionary mappings.
- Sentence outputs are draft candidates unless they already match approved reviewed data.
- Unknown words are marked as unknown; the system does not invent Coptic terms.
- Low evidence lowers confidence and returns a human-review warning.
- Responses include references/evidence from database records where available.
- Reviewer correction/approval creates a source-backed approved example, making future exact sentence matches return approved output.
