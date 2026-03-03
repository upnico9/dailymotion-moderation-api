CREATE TABLE IF NOT EXISTS videos_queue (
    video_id            VARCHAR(50) PRIMARY KEY,
    status              VARCHAR(20) NOT NULL DEFAULT 'pending',
    assigned_moderator  VARCHAR(255) NULL,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS video_logs (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    video_id    VARCHAR(50) NOT NULL REFERENCES videos_queue(video_id),
    status      VARCHAR(20) NOT NULL,
    moderator   VARCHAR(255) NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_videos_pending
    ON videos_queue(created_at) WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_video_logs_video_id
    ON video_logs(video_id);
