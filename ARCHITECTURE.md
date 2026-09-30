# Arabic to Coptic Translator - Technical Architecture

وثيقة تصميم تقنية لتطبيق ترجمة من العربية إلى القبطية. الهدف هو بناء نظام موثوق لا يخترع ألفاظاً قبطية بلا مصدر، ويفصل بوضوح بين ترجمة الكلمة من القاموس وترجمة الجملة كناتج مرشح يحتاج مراجعة بشرية.

## 0. Implementation Status

المشروع الحالي يحتوي بالفعل على أساس قابل للتشغيل:

| Area | Status | Notes |
|---|---:|---|
| Backend FastAPI | Done | Routers: auth, public, admin, review, retrieval |
| PostgreSQL schema | Done | SQLAlchemy + Alembic + pgvector fields |
| Translation pipeline | Done | Word lookup + sentence candidate + confidence + evidence |
| RAG retrieval | Done | pgvector-compatible embeddings + full-text/fallback similarity |
| Admin panel | Done | Next.js admin pages, CRUD, review queue, audit logs |
| Web translator | Done | `/translate` page with confidence, references, unknown words |
| Mobile app | Done | Expo starter: login, dialect selector, translation result |
| Review feedback loop | Done | Approved/corrected candidates become approved `parallel_segments` |
| Tests | Done | pytest coverage for translation, retrieval, admin workflows |
| Docker | Partial runtime | Compose config exists; runtime needs Docker daemon running |

This document is the target architecture and also reflects the current implementation names where possible.

---

## 1. System Architecture

### 1.1 Architectural Style

The system is a modular monolith:

```text
Clients
  Next.js Web/Admin
  Expo Mobile
      |
      | HTTPS + JWT Bearer
      v
FastAPI Backend
  API Routers
  Services
  TranslationService
  RetrievalService
  ReviewService
      |
      v
PostgreSQL 16 + pgvector + pg_trgm
```

This is intentionally not microservices for MVP. The knowledge base, review workflow, and translation pipeline need transactional consistency more than independent deployment.

### 1.2 Runtime Components

| Component | Responsibility | Current Tech |
|---|---|---|
| Web app | Authenticated translator + admin panel | Next.js + TypeScript + React Query + Zod |
| Mobile app | Mobile translator experience | React Native Expo |
| API backend | REST API, auth, RBAC, translation, review | FastAPI + SQLAlchemy |
| Database | Canonical dictionary/corpus/grammar/review store | PostgreSQL + pgvector |
| Retrieval layer | Similar examples, meaning matches, grammar matches | `RetrievalService` |
| Translation layer | Word and sentence translation decisions | `TranslationService` |
| Review layer | Human approval/rejection/correction | `ReviewService` |
| Seed layer | Development data | `app.seed.run` |

### 1.3 Hard Constraints

| Constraint | Architectural Rule |
|---|---|
| A single word is translated from dictionary only | Route input to `translate_word`; do not call sentence composer |
| A sentence uses dictionary + corpus + grammar + retrieval | Route input to `translate_sentence` and persist candidate |
| No new sentence translation is approved automatically | New `translation_candidates.review_status = draft` |
| Dialects must be supported | `dialects` table and `dialect_id` on dictionary/corpus/grammar/candidates |
| Bohairic is default | Seed/config defaults to Bohairic; UI should preselect it |
| Every translation must expose source and confidence | Response includes `confidence`, `references`, and `evidence`; approved examples require `source_id` |
| Do not hallucinate unknown Coptic words | Unknown tokens remain unknown and lower confidence |

---

## 2. Modules

### 2.1 Backend Modules

| Module | Files | Responsibility |
|---|---|---|
| API routers | `backend/app/api/*.py` | HTTP endpoints and role guards |
| Auth/security | `backend/app/security.py`, `backend/app/deps.py` | JWT, password hashing, current user, RBAC |
| Models | `backend/app/models/*.py` | SQLAlchemy entities |
| Schemas | `backend/app/schemas/*.py` | Pydantic request/response contracts |
| Dictionary service | `backend/app/services/dictionary.py` | Search, public lookup, dictionary CRUD |
| Translation service | `backend/app/services/translation.py` | Word/sentence pipeline orchestration |
| Retrieval service | `backend/app/services/retrieval.py` | Similar segments, meanings, grammar references |
| Review service | `backend/app/services/review.py` | Approve/reject/correct candidates |
| Admin service | `backend/app/services/admin.py` | Admin CRUD, embeddings, audit logs |
| Embedding service | `backend/app/services/embedding.py` | Deterministic dev embeddings |
| Text service | `backend/app/services/text.py` | Arabic normalization/tokenization |
| Seed | `backend/app/seed/run.py` | Idempotent development seed data |

### 2.2 Web Modules

| Module | Files | Responsibility |
|---|---|---|
| App shell | `web/src/components/app-shell.tsx` | Sidebar/topbar/navigation |
| Protected routes | `web/src/components/protected-route.tsx` | Client-side role gating |
| API client | `web/src/lib/api.ts` | Fetch wrapper with JWT |
| Auth storage | `web/src/lib/auth.ts` | Session persistence |
| Resource configs | `web/src/lib/resource-config.ts` | Admin page metadata, Zod schemas |
| Resource pages | `web/src/components/resource-page.tsx` | Generic CRUD UI |
| Review queue | `web/src/app/review-queue/page.tsx` | Reviewer approve/reject/correct |
| Translator page | `web/src/app/translate/page.tsx` | User translation flow |

### 2.3 Mobile Modules

| Module | Files | Responsibility |
|---|---|---|
| Expo app | `mobile/App.tsx` | Login, dialect selection, translation UI |
| API client | `mobile/src/api.ts` | Mobile REST calls |

---

## 3. Database Design

### 3.1 Database Extensions

Required PostgreSQL extensions:

- `vector` for pgvector columns.
- `pg_trgm` for trigram text search.
- `citext` reserved for case-insensitive text where needed.

### 3.2 Core Tables

| Table | Purpose |
|---|---|
| `users` | Login identities, role, preferred dialect |
| `roles`, `user_roles` | Role records and future many-to-many support |
| `dialects` | Coptic dialects such as Bohairic and Sahidic |
| `sources` | Books, lexicons, manuscripts, websites, papers |
| `dictionary_entries` | Coptic words, dialect, source, part of speech |
| `arabic_senses` | Arabic lemma plus meaning/definition |
| `sense_mappings` | Many-to-many mapping from Arabic senses to Coptic entries |
| `corpus_texts` | Source-backed corpus documents |
| `parallel_segments` | Arabic/Coptic aligned examples |
| `grammar_rules` | Dialect-specific grammar rules and examples |
| `translation_requests` | User submitted text |
| `translation_candidates` | Generated or reviewed candidate translations |
| `translation_reviews` | Reviewer actions and comments |
| `audit_logs` | Administrative create/update/delete traces |

### 3.3 Key Relationships

```text
dialects 1--N dictionary_entries
sources  1--N dictionary_entries

arabic_senses N--N dictionary_entries
  via sense_mappings

sources 1--N corpus_texts
corpus_texts 1--N parallel_segments
dialects 1--N parallel_segments

translation_requests 1--N translation_candidates
translation_candidates 1--N translation_reviews

reviewed translation_candidate
  -> approved parallel_segment
  -> future retrieval / exact approved sentence match
```

### 3.4 Important Fields

#### `dictionary_entries`

- `coptic_text`
- `normalized_coptic_text`
- `transliteration`
- `dialect_id`
- `source_id`
- `part_of_speech`
- `example_sentence`
- `example_embedding`
- `review_status`

Rule: every Coptic word must have `source_id`, `dialect_id`, and `part_of_speech`.

#### `arabic_senses`

- `arabic_lemma`
- `normalized_arabic_lemma`
- `definition_ar`
- `part_of_speech`
- `example_ar`
- `meaning_embedding`
- `source_id`
- `review_status`

Rule: one Arabic lemma can have multiple senses.

#### `sense_mappings`

- `arabic_sense_id`
- `dictionary_entry_id`
- `confidence`
- `is_primary`
- `review_status`

Rule: one sense can map to multiple Coptic entries.

#### `parallel_segments`

- `arabic_text`
- `coptic_text`
- `source_id`
- `dialect_id`
- `arabic_embedding`
- `coptic_embedding`
- `sentence_embedding`
- `review_status`

Rule: approved sentence examples must be source-backed.

#### `grammar_rules`

- `title`
- `rule_code`
- `description`
- `description_embedding`
- `pattern`
- `replacement`
- `examples`
- `priority`
- `dialect_id`
- `source_id`
- `review_status`

#### `translation_candidates`

- `translation_request_id`
- `candidate_text`
- `dialect_id`
- `generated_by`
- `confidence`
- `evidence`
- `review_status`

Rule: new AI-generated sentence candidates default to `draft`.

The `source` requirement is represented through `evidence.references`, dictionary entry source IDs, and approved `parallel_segments.source_id`. If a candidate is approved/corrected, it is written back to `parallel_segments` with `source_id`.

### 3.5 Indexing Strategy

| Table | Indexes |
|---|---|
| `dictionary_entries` | dialect, source, part of speech, review status, Coptic trigram, example vector |
| `arabic_senses` | normalized lemma, lemma trigram, meaning vector |
| `sense_mappings` | sense ID, dictionary entry ID, confidence |
| `parallel_segments` | source, dialect, review status, Arabic trigram, Coptic trigram, Arabic/Coptic/sentence vectors |
| `grammar_rules` | dialect, review status, description vector |
| `translation_requests` | user, status, input trigram |
| `translation_candidates` | request, review status, candidate trigram |
| `audit_logs` | user, table+record |

---

## 4. Translation Pipeline

### 4.1 Input Routing

```text
POST /translate
  normalize Arabic
  if one token:
    word translation
  else:
    sentence translation
```

### 4.2 Word Translation

Steps:

1. Normalize Arabic input.
2. Confirm it is a single word.
3. Query `arabic_senses.normalized_arabic_lemma`.
4. Join approved `sense_mappings`.
5. Join approved `dictionary_entries`.
6. Filter by requested dialect if provided.
7. Return all mapped Coptic entries.

Response includes:

- Coptic word.
- Dialect.
- Part of speech.
- Arabic meaning.
- Source.
- Mapping confidence.
- Examples.
- References.

No AI generation happens for word translation.

### 4.3 Sentence Translation

Steps:

1. Normalize Arabic sentence.
2. Check exact approved `parallel_segments.normalized_arabic_text`.
3. If exact approved match exists, return approved translation.
4. Tokenize Arabic.
5. Lookup each token through the dictionary pipeline.
6. Mark missing words as `unknown`.
7. Retrieve similar examples from `parallel_segments`.
8. Retrieve relevant Arabic meanings from `arabic_senses`.
9. Retrieve matching grammar rules from `grammar_rules`.
10. Compose a candidate only from known dictionary entries.
11. Calculate confidence.
12. Save `translation_request`.
13. Save `translation_candidate` as `draft`.

### 4.4 No-Hallucination Rules

- Unknown Arabic tokens are not translated.
- If any required word is unknown, `candidate_translation` can be `null`.
- Low evidence lowers confidence.
- If confidence is below threshold, response says human review is needed.
- The composer cannot invent Coptic words not present in dictionary mappings.

### 4.5 Confidence Model

Confidence is calculated from:

| Signal | Effect |
|---|---|
| Token coverage | Higher when all tokens are known |
| Mapping confidence | Based on `sense_mappings.confidence` |
| Similar examples | Higher if retrieved examples are close |
| Meaning matches | Helps sense evidence |
| Grammar notes | Small positive signal |
| Unknown words | Strong penalty |
| No examples | Evidence penalty |

Output range: `0.0` to `0.95` for new candidates, `1.0` for exact approved sentence matches.

---

## 5. RAG / Retrieval Layer

### 5.1 Embedding Targets

Embeddings are stored for:

- `parallel_segments.arabic_text` -> `arabic_embedding`
- `parallel_segments.coptic_text` -> `coptic_embedding`
- `parallel_segments.arabic_text` -> `sentence_embedding`
- `arabic_senses.definition_ar` -> `meaning_embedding`
- `grammar_rules.description` -> `description_embedding`

### 5.2 Retrieval Responsibilities

`RetrievalService` returns:

- Top similar Arabic/Coptic parallel segments.
- Relevant Arabic sense examples.
- Relevant grammar rules.
- DB references used by the translation response.

### 5.3 Required Output References

Every sentence response should expose `references`, for example:

```json
[
  {"table": "dictionary_entries", "id": 12},
  {"table": "parallel_segments", "id": 7},
  {"table": "grammar_rules", "id": 3}
]
```

If references are too weak or absent, confidence must be low.

---

## 6. Admin Review Workflow

### 6.1 State Model

```text
translation_candidate
  draft
    | approve
    v
  approved

  draft
    | reject
    v
  rejected

  draft
    | correct + approve
    v
  approved with corrected_text
```

### 6.2 Reviewer Actions

| Action | Endpoint | Result |
|---|---|---|
| Approve | `POST /review/translation/{id}/approve` | candidate becomes `approved` |
| Reject | `POST /review/translation/{id}/reject` | candidate becomes `rejected` |
| Correct | `POST /review/translation/{id}/correct` | candidate text replaced and approved |

### 6.3 Feedback Loop

When a candidate is approved or corrected:

1. Read original Arabic from `translation_requests`.
2. Read final Coptic from `translation_candidates`.
3. Derive a source from evidence or an existing source.
4. Insert approved `parallel_segments`.
5. Future exact sentence matches can return approved output.

This prevents a reviewed sentence from being regenerated as an unreviewed draft.

### 6.4 Admin Data Workflow

Admin can manage:

- Dictionary entries.
- Arabic senses.
- Sense mappings.
- Corpus texts.
- Parallel segments.
- Grammar rules.
- Sources.
- Users and roles.
- Audit logs.

All create/update/delete actions should be auditable.

---

## 7. Web App Pages

Current web app is a protected operational app rather than a public marketing site.

| Route | Role | Purpose |
|---|---|---|
| `/login` | public | JWT login |
| `/` | admin/reviewer | Dashboard: requests, candidates, confidence |
| `/translate` | user/reviewer/admin | Translation input/result |
| `/dictionary` | admin | Dictionary CRUD |
| `/senses` | admin | Arabic sense management |
| `/mappings` | admin | Sense mapping management |
| `/corpus-texts` | admin | Corpus document management |
| `/parallel-segments` | admin | Parallel example management |
| `/grammar-rules` | admin | Grammar rule management |
| `/sources` | admin | Source management |
| `/users-roles` | admin | User/role management |
| `/audit-logs` | admin | Audit trail |
| `/translation-requests` | reviewer/admin | Request inspection |
| `/review-queue` | reviewer/admin | Approve/reject/correct candidates |

### 7.1 UI Requirements

- Tables with search, pagination, and filters.
- Filters by dialect, review status, source, confidence, and created date.
- Zod validation for forms.
- React Query for data fetching/mutations.
- Protected routes by role.
- Evidence and references visible in review queue.

---

## 8. Mobile App Screens

MVP mobile app:

| Screen/State | Purpose |
|---|---|
| Login | Authenticate and store access token in state |
| Translator | Arabic input, dialect selection, submit |
| Result | Translation/candidate, confidence, warning, evidence |
| Evidence blocks | Literal breakdown, dictionary words, similar examples, grammar notes, references |

Future mobile navigation:

```text
Translate
Dictionary Browse
Examples
Favorites
Profile / Preferred Dialect
```

For MVP, mobile is read/translate only. Admin and review actions remain web-only.

---

## 9. API Endpoints

### 9.1 Auth

| Method | Path | Role |
|---|---|---|
| POST | `/auth/login` | public |

### 9.2 Public/User

| Method | Path | Role | Notes |
|---|---|---|---|
| POST | `/translate` | authenticated | Word or sentence translation |
| GET | `/dictionary/search?q=` | public | Approved dictionary search |
| GET | `/dictionary/{id}` | public | Approved entry detail |
| GET | `/examples/search?q=` | public | Similar approved examples |
| GET | `/dialects` | public | Active dialects |

### 9.3 Retrieval

| Method | Path | Role |
|---|---|---|
| POST | `/retrieval/similar-segments` | authenticated |

### 9.4 Admin

| Method | Path |
|---|---|
| GET/POST | `/admin/dictionary` |
| PUT/DELETE | `/admin/dictionary/{id}` |
| GET/POST | `/admin/senses` |
| PUT/DELETE | `/admin/senses/{id}` |
| GET/POST | `/admin/mappings` |
| PUT/DELETE | `/admin/mappings/{id}` |
| GET/POST | `/admin/corpus-texts` |
| PUT/DELETE | `/admin/corpus-texts/{id}` |
| GET/POST | `/admin/parallel-segments` |
| PUT/DELETE | `/admin/parallel-segments/{id}` |
| GET/POST | `/admin/grammar-rules` |
| PUT/DELETE | `/admin/grammar-rules/{id}` |
| GET/POST | `/admin/sources` |
| PUT/DELETE | `/admin/sources/{id}` |
| GET/POST | `/admin/users` |
| PUT/DELETE | `/admin/users/{id}` |
| GET | `/admin/audit-logs` |
| GET | `/admin/translation-requests` |
| GET | `/admin/translation-candidates` |

### 9.5 Reviewer

| Method | Path |
|---|---|
| GET | `/review/translation-requests` |
| GET | `/review/translation-candidates` |
| POST | `/review/translation/{id}/approve` |
| POST | `/review/translation/{id}/reject` |
| POST | `/review/translation/{id}/correct` |

---

## 10. Security Requirements

### 10.1 Authentication

- JWT bearer access token.
- Passwords hashed with Passlib context.
- Login must never disclose whether email or password failed.

### 10.2 Authorization

Roles:

- `user`: translate and inspect public resources.
- `reviewer`: user permissions plus review queue actions.
- `admin`: full CRUD and audit access.

All admin routes require `Role.admin`.
Review routes require `Role.reviewer` or `Role.admin`.

### 10.3 API Safety

- Strict Pydantic schemas.
- SQLAlchemy query construction; no raw string-concatenated SQL.
- CORS controlled by config.
- Production should add rate limits for login and translate.
- Production should use HTTPS only.

### 10.4 Data Safety

- Do not send private user data to an LLM provider.
- LLM composer is optional and must be evidence-gated.
- Audit logs should track admin mutations.
- Backups should include DB plus migration history.

---

## 11. Data Validation

### 11.1 Input Validation

| Input | Rule |
|---|---|
| Translate text | Non-empty, normalized before processing |
| Dialect | Must exist and be active |
| Coptic dictionary entry | Must include text, dialect, source, part of speech |
| Arabic sense | Must include lemma and definition |
| Mapping confidence | 0..1 |
| Parallel segment | Must include Arabic text and source; Coptic text required for approved example |
| Grammar rule | Must include title and description |
| Candidate confidence | 0..1 |
| Review correction | Non-empty corrected Coptic text |

### 11.2 Normalization

Arabic normalization should:

- Remove diacritics.
- Normalize alef variants.
- Normalize ya/alef maqsura.
- Normalize ta marbuta consistently.
- Trim duplicate whitespace.

The normalized form is used for lookup, matching, and exact approved sentence reuse.

### 11.3 Review Validation

Before a translation can be treated as approved:

- It must be tied to a source via evidence or approved parallel segment.
- It must be approved/corrected by reviewer/admin.
- It should be saved as `parallel_segments.review_status = approved`.

---

## 12. Deployment Plan

### 12.1 Local Development

```bash
docker compose up --build
```

Services:

- `db`: pgvector PostgreSQL.
- `backend`: FastAPI; runs Alembic and seed.
- `web`: Next.js admin/web.

### 12.2 Backend Startup

Container command:

```bash
alembic upgrade head && python -m app.seed.run && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 12.3 Environment Variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy DB connection |
| `JWT_SECRET` | JWT signing secret |
| `JWT_ALGORITHM` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime |
| `BACKEND_CORS_ORIGINS` | Allowed web origins |
| `NEXT_PUBLIC_API_BASE_URL` | Web API base URL |
| `EXPO_PUBLIC_API_BASE_URL` | Mobile API base URL |

### 12.4 Production Plan

- Use managed PostgreSQL with pgvector if available.
- Run migrations as a release job.
- Serve backend behind reverse proxy.
- Serve Next.js as standalone container.
- Build Expo app via EAS.
- Enable HTTPS, rate limiting, structured logs, monitoring, DB backups.

---

## 13. MVP Scope

### 13.1 In MVP

- Bohairic default dialect.
- Sahidic-ready schema.
- JWT login.
- Roles: user, reviewer, admin.
- Word translation from dictionary.
- Sentence draft generation through dictionary + retrieval + grammar.
- No-hallucination behavior for unknown words.
- Confidence score and evidence references.
- Admin CRUD for linguistic data.
- Review queue.
- Correct/approve/reject actions.
- Approved review feedback into corpus.
- Web translator and admin panel.
- Expo mobile translator starter.
- Docker Compose.
- Seed data.
- pytest test suite.

### 13.2 Out of MVP

- Production-grade scholarly corpus.
- Full Coptic morphology/conjugation engine.
- Community contribution workflow.
- Offline mobile dictionary cache.
- Full bidirectional Coptic -> Arabic translation.
- LLM composer in production.
- OCR for manuscripts.
- Audio/TTS.

### 13.3 MVP Acceptance Criteria

1. A known Arabic word returns sourced Coptic dictionary entries.
2. A sentence with known words returns a draft candidate with evidence and confidence.
3. A sentence with unknown words does not fabricate a full Coptic translation.
4. A new sentence candidate is never returned as approved before review.
5. Reviewer correction creates an approved parallel segment.
6. Future exact match can return the approved reviewed sentence.
7. Admin CRUD and audit logs work.
8. Backend tests pass.
9. Web typecheck/build pass.
10. Mobile typecheck passes.

---

## 14. Future Roadmap

### Phase 1 - Data Quality (Completed)

- [x] Replace seed data with curated lexicon entries.
- [x] Add source metadata for standard references.
- [x] Add import pipeline for TEI/CSV/JSON dictionary data.
- [x] Add duplicate detection for Arabic senses and Coptic entries.

### Phase 2 - Linguistic Depth (Completed)

- [x] Add morphology engine for Coptic nouns/verbs (`VerbConjugator`, `NounDeclension`).
- [x] Add grammatical gender/number agreement checks in syntax composer.
- [x] Add dialect-specific grammar priority (Bohairic vs Sahidic particles & conjugations).
- [x] Add sentence-type detection (nominal vs verbal vs negative with copula resolution).

### Phase 3 - Retrieval Quality (Completed)

- [x] Replace deterministic dev embeddings with multilingual embedding model (`SentenceTransformerEmbeddingProvider`, LRU cache, and fallback).
- [x] Add hybrid ranking: trigram + vector + source quality + review status (`RetrievalService` with comprehensive score breakdown).
- [x] Store reviewer feedback as training/evaluation data (`EvaluationDatasetService` with JSONL/CSV exports and admin metrics).

### Phase 4 - Product Features (Completed)

- [x] Public dictionary browsing with Coptic alphabet and POS filtering (`/dictionary/browse`).
- [x] Favorites and translation history with Freemium daily quota enforcement.
- [x] Reviewer workload dashboard with individual reviewer statistics (`/admin/workload`).
- [x] Bulk admin export for dictionary and parallel segments (CSV / JSON).
- [x] Source citation pages with bibliographic data and one-click citation copy (`/sources`).
- [x] Mobile offline cache with automatic fallback for network interruptions (`storage.ts` & `api.ts`).

### Phase 5 - Advanced AI

- Evidence-gated LLM composer.
- Prompt templates that forbid unsupported words.
- Automatic critique before draft save.
- Evaluation suite against approved corpus.

---

## 15. Engineering Rules

- Prefer deterministic dictionary/retrieval output over generative output.
- Keep all new sentence translations as `draft`.
- Every user-visible translation must show confidence and evidence.
- Every approved Coptic sentence must be source-backed.
- Unknown tokens remain unknown.
- Admin edits should be auditable.
- Tests must cover translation safety, review workflow, retrieval, and admin CRUD.
