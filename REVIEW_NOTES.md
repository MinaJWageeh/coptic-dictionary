# Coptic_Dic Project Review Notes

## Fails / Bugs

### Backend

- [x] **1. FIXED** — TranslationService.translate_sentence — empty candidate_text stored as `""` instead of `null`. `candidate_text` nullable now; `None` stored when the pipeline cannot compose a safe candidate. Model (`models/translation.py`), Alembic migration `20260624_0003`, schemas (`review.py`, `admin.py`), and service (`translation.py`) all updated.

- [x] **2. FIXED** — ReviewService.correct — `normalized_candidate_text` now uses `normalize_coptic(corrected_text)` instead of raw corrected text. (`services/review.py`)

- [x] **3. FIXED** — ReviewService._source_id_from_evidence — arbitrary `Source.id == 1` fallback removed; returns `None` when no derivable source, preventing wrong source attribution on approval. (`services/review.py`)

- [x] **4. FIXED** — Admin API list endpoints now filter `review_status == approved` for DictionaryEntry, ArabicSense, SenseMapping, CorpusText, ParallelSegment, GrammarRule. Sources (no review_status) and TranslationRequest/Candidate (need drafts for review) left unfiltered. (`api/admin.py`)

- [x] **5. FIXED** — Removed the pivot fallback that used a similar parallel segment's Coptic text when the pipeline produced no candidate. Unknown-word inputs now correctly return `null` candidate_text instead of an unrelated segment's translation. (`services/translation.py`)

- [x] **6. FIXED** — `RetrievalService._is_postgres` now uses `self.db.get_bind().dialect.name` for SQLAlchemy 2.0 compatibility. (`services/retrieval.py`)

- [x] **7. FIXED** — Word translation now returns all mapped Coptic entries joined with " / " in `translation` (deduplicated), so the field is no longer ambiguous. `word_results` still carries the full per-entry detail. (`services/translation.py`)

- [x] **8. FIXED** — Rate limiting added. `services/rate_limit.py` implements a thread-safe sliding-window limiter that returns HTTP 429 with a `Retry-After` header, applied as a dependency on `/auth/login` (10/min) and `/translate` (60/min) in `api/auth.py` and `api/public.py`. Covered by `tests/test_points_8_to_10.py`.

- [x] **9. FIXED** — `TranslationCandidate.generated_by` now records `"rule_based"` instead of `"ai"`, reflecting the dictionary/syntax composition pipeline. (`services/translation.py`)

- [x] **10. FIXED** — Token errors no longer leak user existence: `get_current_user` and `get_optional_current_user` both return `"Invalid token"` for a bad token and for a valid token with no matching user; the `"User not found"` message was removed. (`deps.py`)

### Web Frontend

- [x] **11. FIXED** — `inferRole` reads the role from the JWT payload first and falls back to a strict `startsWith("admin@")` / `startsWith("reviewer@")` match instead of the loose `email.includes("admin")` substring test. (`web/src/lib/auth.ts`)

- [x] **12. FIXED** — Translate form `target_dialect_id` is now `.optional()` and the submit handler maps a falsy `selectedDialectId` to `undefined`, so an empty dialect selection no longer fails Zod validation. (`web/src/app/translate/page.tsx`)

- [x] **13. FIXED** — Frontend low-confidence warning now uses `< 0.6`, matching the backend `LOW_CONFIDENCE_THRESHOLD = 0.6`. (`web/src/components/translation-result-card.tsx`)

### Mobile

- [x] **14. FIXED** — `mobile/App.tsx` now renders `<RootLayout />` instead of returning `null`. (`mobile/App.tsx`)

- [x] **15. FIXED** — `apiFetch` now takes an `ApiFetchOptions` object with an optional `token` field (plus a legacy `tokenArg`), replacing the confusing positional token parameter. (`mobile/src/api.ts`)

### Tests / Docs

- [x] **16. FIXED** — Test users are seeded with `"ChangeMe123!"` (matching the README); `auth_header` keeps a `"secret"` → `"ChangeMe123!"` fallback for backward compatibility. Covered by `tests/test_points_16_to_18.py`. (`tests/conftest.py`)

- [x] **17. FIXED** — `test_translation_service.py` helpers now resolve `dialect_id`/`source_id` dynamically via `_get_dialect_and_source()` instead of hardcoding `1`. Covered by `tests/test_points_16_to_18.py`.

### Data / Schema

- [x] **18. FIXED** — Seed mapping confidences raised to 0.90–0.95 (was 0.4–0.55), so seeded entries no longer fall below the review threshold. Covered by `tests/test_points_16_to_18.py`. (`seed/run.py`)

- [x] **19. FIXED** — Seeded parallel segments now use `alignment_score = 0.95` (was a constant 0.35). Covered by `tests/test_points_16_to_18.py`. (`seed/run.py`)

## Future Enhancements / Updates

### Phase 1 - Data Quality (from ARCHITECTURE.md §14)
- [x] Replace seed data with curated lexicon entries (source-backed, scholarly) — done (`seed/data/curated_lexicon.py`, `seed/run.py`)
- [x] Add source metadata for standard references (Liddell-Scott, Bailly, etc.) — done (`services/sources.py`)
- [x] Add import pipeline for TEI/CSV/JSON dictionary data — done (`services/import_pipeline.py`, `api/admin.py`)
- [x] Add duplicate detection for Arabic senses and Coptic entries — done (`services/deduplication.py`, `api/admin.py`)

### Phase 2 - Linguistic Depth
- [x] Full Coptic morphology/conjugation engine (noun declensions, verb conjugation) — done (`services/morphology.py`)
- [x] Grammatical gender/number agreement checks in composer — done (`services/syntax.py`, `services/sentence_analysis.py`)
- [x] Dialect-specific grammar priority (Bohairic vs Sahidic vs Fayyumic) — done (`services/syntax.py`)
- [x] Sentence-type detection (nominal vs verbal vs negative) — done (`services/sentence_analysis.py`, `services/syntax.py`)

### Phase 3 - Retrieval Quality
- [x] Replace deterministic `embed_text` with multilingual embedding model (e.g., paraphrase-multilingual-MiniLM-L12-v2) — done (`services/embedding.py`: provider abstraction + `EmbeddingManager` with LRU cache and deterministic fallback)
- [x] Hybrid ranking: trigram + vector + source quality + review status — done (`services/retrieval.py`: `compute_hybrid_ranking`, `compute_trigram_overlap`, `get_source_quality_score`, `get_review_status_score`)
- [x] Store reviewer feedback as training/evaluation data — done (`services/evaluation.py`, `api/admin.py`: `/admin/evaluation/metrics`, `/admin/evaluation/dataset` JSON/JSONL/CSV)

### Phase 4 - Product Features
- [x] Public dictionary browsing (no auth required) — done (`api/public.py`: `/dictionary/browse` with search, letter, dialect, POS, pagination)
- [x] Favorites and translation history — done (`mobile/src/storage.ts`: `saveFavorite`/`listFavorites`, `saveLastTranslation`/`getLastTranslation`)
- [x] Reviewer workload dashboard — done (`api/admin.py`: `GET /admin/workload` with per-reviewer stats)
- [x] Bulk admin import/export (CSV/JSON) — done (`api/admin.py`: `GET /admin/export/dictionary`, `GET /admin/export/segments`)
- [x] Source citation pages with bibliographic data — done (`api/public.py`: `/sources` + `web/src/app/sources/page.tsx` with `citation_text` copy)
- [x] Mobile offline cache — done (`mobile/src/storage.ts`: `getCachedResponse`/`setCachedResponse` with fallback)

### Phase 5 - Advanced AI
- [ ] Evidence-gated LLM composer (optional, gated by confidence threshold)
- [ ] Prompt templates that forbid unsupported words
- [ ] Automatic critique before draft save
- [ ] Evaluation suite against approved corpus

### Engineering / Ops
- [x] Add rate limiting (login, translate endpoints) — done, see bug #8
- [ ] Add HTTPS enforcement and secure JWT settings in production
- [ ] Structured logging and monitoring (Sentry/OpenTelemetry)
- [ ] DB backup strategy with migration history included
- [ ] CI/CD pipeline with typecheck, lint, test, build gates
- [x] Replace `inferRole` email-substring heuristic with server-provided role in JWT — done, see bug #11 (JWT payload role is now primary)
- [ ] Add API versioning (`/api/v1/...` prefix — config has `API_V1_PREFIX` but routers don't use it)
- [x] Migrate SQLAlchemy `db.bind` to `db.get_bind()` for 2.0 compat — done, see bug #6
- [x] Align frontend `lowConfidence` threshold (0.55) with backend `LOW_CONFIDENCE_THRESHOLD` (0.6) — done, see bug #13
- [ ] Add pagination to all list endpoints (currently no limit/offset)
- [ ] Add full-text search index on `translation_requests.normalized_input_text`
- [ ] Add `TranslationCandidate.generated_by` values: `dictionary`, `composition`, `ai` (currently set to `rule_based`, see bug #9)
- [ ] Add soft-delete support (Base has `deleted_at` column but no service uses it)
- [ ] Add Coptic -> Arabic reverse translation (out of MVP, Phase 5+)
- [ ] Add OCR for manuscript images (Phase 5+)
- [ ] Add TTS / audio for Coptic pronunciation
- [ ] Add community contribution workflow with moderation
