# Architecture Diagrams — Moderation API

## 1. Vue d'ensemble du système

```mermaid
graph TB
    UI["Moderation Console UI</i>"]

    subgraph Docker Compose
        MQ["Moderation Queue API"]
        DP["Dailymotion API Proxy"]
        PG[("PostgreSQL<br/>port 5432")]
    end

    EXT["Dailymotion Public API<br/>api.dailymotion.com"]

    UI -- "POST /add_video<br/>GET /get_video<br/>POST /flag_video<br/>GET /stats<br/>GET /log_video/{id}" --> MQ
    UI -- "GET /get_video_info/{id}" --> DP
    MQ --> PG
    DP -- "HTTP GET /video/{id}<br/>" --> EXT

    style UI fill:#e8eaf6,stroke:#3f51b5
    style MQ fill:#e3f2fd,stroke:#1976d2
    style DP fill:#e8f5e9,stroke:#388e3c
    style PG fill:#fff3e0,stroke:#f57c00
    style EXT fill:#fce4ec,stroke:#c62828
```

---

## 2. Architecture en couches — Moderation Queue

```mermaid
graph LR
    subgraph Routes
        direction TB
        R1["add_video · stats"]
        R2["get_video · flag_video"]
        R3["log_video"]
    end

    AUTH["Auth<br/>Middleware"]
    MS["Moderation<br/>Service"]
    ED["Event<br/>Dispatcher"]
    VLS["VideoLog<br/>Service"]
    DOM["Domain"]
    VR["Video<br/>Repository"]
    VLR["VideoLog<br/>Repository"]
    PG[("PostgreSQL")]

    R2 --> AUTH
    AUTH --> MS
    R1 --> MS
    R3 --> VLS
    MS --> ED --> VLS
    MS -.-> DOM
    MS --> VR --> PG
    VLS --> VLR --> PG

    style MS fill:#e3f2fd,stroke:#1976d2
    style VLS fill:#e3f2fd,stroke:#1976d2
    style ED fill:#fff3e0,stroke:#f57c00
    style AUTH fill:#fff9c4,stroke:#f9a825
    style VR fill:#f3e5f5,stroke:#7b1fa2
    style VLR fill:#f3e5f5,stroke:#7b1fa2
    style PG fill:#fff3e0,stroke:#f57c00
    style DOM fill:#e8f5e9,stroke:#388e3c
```

---

## 3. Architecture en couches — Dailymotion Proxy

```mermaid
graph TB
    subgraph "Routes"
        R["GET /get_video_info/{video_id}"]
    end

    subgraph "Services"
        PS["ProxyService"]
    end

    subgraph "Infrastructure"
        DC["DailymotionClient<br/><i>requests HTTP</i>"]
        VC["VideoCache<br/><i>In-memory + TTL</i>"]
        EH["Error Handler"]
    end

    subgraph "Domain"
        EXC["Exceptions"]
    end

    EXT["Dailymotion API"]

    R --> PS
    PS --> VC
    PS --> DC
    PS --> EXC
    DC --> EXT

    style PS fill:#e8f5e9,stroke:#388e3c
    style VC fill:#fff3e0,stroke:#f57c00
    style DC fill:#e3f2fd,stroke:#1976d2
    style EXT fill:#fce4ec,stroke:#c62828
```

---

## 4. Schéma de la base de données

```mermaid
erDiagram
    videos_queue {
        VARCHAR50 video_id PK "Dailymotion video ID"
        VARCHAR20 status "pending | spam | not spam"
        VARCHAR255 assigned_moderator "NULL si non assignée"
        TIMESTAMP created_at "DEFAULT NOW()"
        TIMESTAMP updated_at "DEFAULT NOW()"
    }

    video_logs {
        INTEGER id PK "GENERATED ALWAYS AS IDENTITY"
        VARCHAR50 video_id FK "→ videos_queue.video_id"
        VARCHAR20 status "Status au moment du log"
        VARCHAR255 moderator "NULL si aucun modérateur"
        TIMESTAMP created_at "DEFAULT NOW()"
    }

    videos_queue ||--o{ video_logs : "historique"
```

**Index** :
- `idx_videos_pending` — `videos_queue(created_at) WHERE status = 'pending'` → accélère le FIFO
- `idx_video_logs_video_id` — `video_logs(video_id)` → accélère l'audit

---

## 5. Système d'événements (Event-Driven Logging)

```mermaid
graph LR
    subgraph "ModerationService"
        A1["add_video()"]
        A2["get_video()"]
        A3["flag_video()"]
    end

    subgraph "Domain Events"
        E1["VideoAdded"]
        E2["VideoAssigned"]
        E3["VideoFlagged"]
    end

    subgraph "EventDispatcher"
        ED["dispatch(event)"]
    end

    subgraph "VideoLogService"
        L1["log_added()"]
        L2["log_assigned()"]
        L3["log_flagged()"]
    end

    subgraph "VideoLogRepository"
        VLR["create(video_id, status, moderator)"]
    end

    DB[("PostgreSQL<br/>video_logs")]

    A1 -->|emit| E1
    A2 -->|emit| E2
    A3 -->|emit| E3
    E1 & E2 & E3 --> ED
    ED -->|listener| L1
    ED -->|listener| L2
    ED -->|listener| L3
    L1 & L2 & L3 --> VLR
    VLR --> DB

    style ED fill:#fff3e0,stroke:#f57c00
    style E1 fill:#e8eaf6,stroke:#3f51b5
    style E2 fill:#e8eaf6,stroke:#3f51b5
    style E3 fill:#e8eaf6,stroke:#3f51b5
```

---

## 6. Stratégie de cache — Dailymotion Proxy

```mermaid
graph TB
    REQ["Requête entrante<br/>GET /get_video_info/{id}"]

    ID_CHECK{"video_id<br/>se termine<br/>par 404 ?"}
    CACHE_CHECK{"Cache<br/>hit ?"}
    TTL_CHECK{"TTL<br/>expiré ?"}

    RETURN_404["HTTP 404<br/>Video not found"]
    RETURN_CACHED["Retourner<br/>données cachées"]
    API_CALL["Appel API<br/>Dailymotion"]
    CACHE_STORE["Stocker en cache<br/>avec TTL"]
    RETURN_DATA["HTTP 200<br/>Données vidéo"]
    EVICT{"Cache plein ?"}
    EVICT_ONE["Évincer l'entrée<br/>la plus ancienne"]

    REQ --> ID_CHECK
    ID_CHECK -->|Oui| RETURN_404
    ID_CHECK -->|Non| CACHE_CHECK
    CACHE_CHECK -->|Hit + TTL valide| RETURN_CACHED
    CACHE_CHECK -->|Miss ou expiré| API_CALL
    API_CALL --> EVICT
    EVICT -->|Oui| EVICT_ONE --> CACHE_STORE
    EVICT -->|Non| CACHE_STORE
    CACHE_STORE --> RETURN_DATA

    style RETURN_404 fill:#ffcdd2,stroke:#c62828
    style RETURN_CACHED fill:#c8e6c9,stroke:#2e7d32
    style RETURN_DATA fill:#c8e6c9,stroke:#2e7d32
    style API_CALL fill:#bbdefb,stroke:#1565c0
```

---
