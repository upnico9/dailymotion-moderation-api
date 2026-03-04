# Moderation API — Dailymotion

Backend de modération vidéo pour Dailymotion. Deux microservices :
- **Moderation Queue** (port 8001) — gestion de la file de modération, assignation FIFO, historique d'audit
- **Dailymotion API Proxy** (port 8002) — proxy vers l'API publique Dailymotion avec cache in-memory

---

## Prérequis

- **Docker** et **Docker Compose** 

---

## Installation et lancement

```bash
git clone <url-du-repo>
cd dailymotion-moderation-api

docker-compose up --build -d
```

Les services sont prêts quand les health checks passent :

| Service | URL | Health check |
|---------|-----|-------------|
| Moderation Queue | http://localhost:8001 | http://localhost:8001/health |
| Dailymotion Proxy | http://localhost:8002 | http://localhost:8002/health |
| PostgreSQL | localhost:5438 | `pg_isready` |

Pour arrêter :

```bash
docker-compose down          # Arrêter (données conservées)
```

---

## Lancement des tests

Tous les tests tournent dans les conteneurs Docker. Un script est fourni :

```bash
chmod +x run_tests.sh
./run_tests.sh
```

Ce script :
1. Build et démarre les services
2. Attend que PostgreSQL, Moderation Queue et Dailymotion Proxy soient prêts
3. Lance `pytest` dans chaque conteneur

Pour lancer les tests manuellement :

```bash
# Tests Moderation Queue
docker-compose exec -T moderation_queue pytest tests/ -v

# Tests Dailymotion Proxy
docker-compose exec -T dailymotion_proxy pytest tests/ -v
```

---

## Routes API

### Moderation Queue — `http://localhost:8001`

#### `POST /add_video`

Ajoute une vidéo à la file de modération (appel server-to-server).

```bash
curl -XPOST http://localhost:8001/add_video \
  -H 'Content-Type: application/json' \
  -d '{"video_id": 123456}'
```

```json
// HTTP 201
{"video_id": "123456"}
```

---

#### `GET /get_video`

Récupère la prochaine vidéo pending pour le modérateur authentifié (FIFO).
Le même modérateur reçoit toujours la même vidéo. Deux modérateurs différents reçoivent des vidéos différentes.

```bash
# "john.doe" encodé en base64 = "am9obi5kb2U="
curl -XGET http://localhost:8001/get_video \
  -H 'Authorization: am9obi5kb2U='
```

```json
// HTTP 200
{"video_id": "123456"}

// HTTP 204 — plus de vidéos en attente
```

---

#### `POST /flag_video`

Le modérateur flag sa vidéo assignée comme `"spam"` ou `"not spam"`.

```bash
curl -XPOST http://localhost:8001/flag_video \
  -H 'Content-Type: application/json' \
  -H 'Authorization: am9obi5kb2U=' \
  -d '{"video_id": "123456", "status": "not spam"}'
```

```json
// HTTP 200
{"video_id": "123456", "status": "not spam"}
```

---

#### `GET /stats`

Statistiques de la file de modération.

```bash
curl -XGET http://localhost:8001/stats
```

```json
// HTTP 200
{
  "total_pending_videos": 42,
  "total_spam_videos": 10,
  "total_not_spam_videos": 85
}
```

---

#### `GET /log_video/{video_id}`

Historique de modération d'une vidéo (audit).

```bash
curl -XGET http://localhost:8001/log_video/123456
```

```json
// HTTP 200
[
  {"date": "2025-01-01 12:00:00", "status": "pending", "moderator": null},
  {"date": "2025-01-01 12:05:00", "status": "pending", "moderator": "john.doe"},
  {"date": "2025-01-01 12:10:00", "status": "not spam", "moderator": "john.doe"}
]
```

---

#### `GET /health`

```bash
curl http://localhost:8001/health
```

```json
{"status": "ok"}
```

---

### Dailymotion API Proxy — `http://localhost:8002`

#### `GET /get_video_info/{video_id}`

Récupère les métadonnées d'une vidéo via l'API Dailymotion (avec cache TTL 5 min).
Les IDs se terminant par `404` retournent une erreur 404.

```bash
curl -XGET http://localhost:8002/get_video_info/x2m8jpp
```

```json
// HTTP 200
{
  "title": "Dailymotion Spirit Movie",
  "channel": "creation",
  "owner": "...",
  "filmstrip_60_url": "...",
  "embed_url": "..."
}
```

```bash
# Vidéo inexistante (ID se termine par 404)
curl -XGET http://localhost:8002/get_video_info/10404
```

```json
// HTTP 404
{"error": "Video 10404 not found"}
```

---

#### `GET /health`

```bash
curl http://localhost:8002/health
```

```json
{"status": "ok"}
```

---

## Codes d'erreur

| Code | Signification |
|------|--------------|
| 201 | Vidéo ajoutée avec succès |
| 200 | Succès |
| 204 | Plus de vidéos en attente |
| 400 | Requête invalide (body manquant, status invalide, vidéo déjà flaggée) |
| 401 | Header Authorization absent ou invalide |
| 403 | Vidéo non assignée à ce modérateur |
| 404 | Vidéo non trouvée |
| 409 | Vidéo déjà dans la file |
| 502 | Erreur API Dailymotion |
| 500 | Erreur interne |

---

## Architecture des fichiers

```
dailymotion-moderation-api/
├── docker-compose.yml              # Orchestration des 3 services
├── run_tests.sh                    # Script de lancement des tests
├── README.md
│
├── moderation_queue/               # Service 1 — File de modération
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── config.py                   
│   ├── app.py                      
│   │
│   ├── domain/                      
│   │   ├── entities.py             
│   │   ├── value_objects.py
│   │   ├── events.py
│   │   └── exceptions.py
│   │
│   ├── repositories/
│   │   ├── video_repository.py     
│   │   └── video_log_repository.py 
│   │
│   ├── services/                   
│   │   ├── moderation_service.py   
│   │   └── video_log_service.py
│   │
│   ├── infrastructure/
│   │   ├── database.py
│   │   ├── event_dispatcher.py
│   │   └── error_handler.py
│   │
│   ├── middleware/
│   │   └── auth.py
│   │
│   ├── routes/
│   │   ├── moderation_routes.py
│   │   └── schemas.py
│   │
│   ├── migrations/
│   │   └── init.sql
│   │
│   └── tests/
│       ├── conftest.py
│       ├── test_domain.py
│       ├── test_events.py
│       ├── test_error_handler.py
│       ├── test_auth.py
│       ├── test_video_repository.py
│       ├── test_video_log_repository.py
│       ├── test_moderation_service.py
│       ├── test_video_log_service.py
│       └── test_routes.py
│
└── dailymotion_proxy/              # Service 2 — Proxy API Dailymotion
    ├── Dockerfile
    ├── requirements.txt
    ├── pyproject.toml
    ├── config.py
    ├── app.py
    │
    ├── domain/
    │   └── exceptions.py
    │
    ├── infrastructure/
    │   ├── cache.py
    │   ├── dailymotion_client.py
    │   └── error_handler.py
    │
    ├── services/
    │   └── proxy_service.py
    │
    ├── routes/
    │   └── proxy_routes.py
    │
    └── tests/
        ├── conftest.py
        ├── test_cache.py
        ├── test_dailymotion_client.py
        └── test_proxy_service.py
```

---

## Choix techniques

| Aspect | Choix |
|--------|-------|
| Framework | **FastAPI** |
| BDD | **PostgreSQL 16** |
| Driver SQL | **psycopg2**|
| Concurrence | **FOR UPDATE SKIP LOCKED** |
| Events | **EventDispatcher maison** |
| Cache | **dict Python in-memory** |
| Tests | **pytest** |
| Conteneurs | **Docker Compose** |
