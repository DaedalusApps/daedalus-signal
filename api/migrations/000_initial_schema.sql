-- Initial Schema for DaedalusSignal
--
-- Reconstructed from code 2026-08-01: the original Flask backend (and its
-- migrations) was deleted before the DreamHost PHP API took over. This file
-- was rebuilt by reading every route in api/routes/, api/lib/, and
-- api/seed.php and inferring columns/types/constraints from how PDO queries
-- use them. Diff against production before relying on it, e.g.:
--   mysqldump --no-data daedalussignal
--
-- Run this BEFORE 001_password_reset_tokens.sql (which FKs to users(id)).
--
-- Index names here are table-prefixed (idx_<table>_<col>), an intentional
-- deviation from 001_password_reset_tokens.sql's unprefixed style, chosen
-- to keep names unique across tables.

-- Registered accounts (auth, digest preferences, admin flag)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    email_verified TINYINT(1) NOT NULL DEFAULT 0,
    digest_enabled TINYINT(1) NOT NULL DEFAULT 1,
    onboarding_complete TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE INDEX idx_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Scrapeable sources (YouTube/Twitter channels, etc.) users can follow
CREATE TABLE IF NOT EXISTS sources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url VARCHAR(500) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    is_default TINYINT(1) NOT NULL DEFAULT 0,
    is_approved TINYINT(1) NOT NULL DEFAULT 0,
    last_scraped DATETIME DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE INDEX idx_sources_url (url),
    INDEX idx_sources_type (source_type),
    INDEX idx_sources_default_approved (is_default, is_approved)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Interest tags users can follow to filter/curate content
CREATE TABLE IF NOT EXISTS tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(100) DEFAULT NULL,
    is_default TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE INDEX idx_tags_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Scraped items (videos/tweets/posts) ingested from sources by the worker
CREATE TABLE IF NOT EXISTS contents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_id INT NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    url VARCHAR(1000) NOT NULL,
    content_type VARCHAR(50) NOT NULL DEFAULT 'article',
    relevance_score INT NOT NULL DEFAULT 50,
    published_at DATETIME DEFAULT NULL,
    scraped_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE,
    UNIQUE INDEX idx_contents_url (url(255)),
    INDEX idx_contents_source_relevance (source_id, relevance_score),
    INDEX idx_contents_scraped_at (scraped_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Join table: which sources each user follows
CREATE TABLE IF NOT EXISTS user_sources (
    user_id INT NOT NULL,
    source_id INT NOT NULL,

    PRIMARY KEY (user_id, source_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE,
    INDEX idx_user_sources_source_id (source_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Join table: which tags each user follows
CREATE TABLE IF NOT EXISTS user_tags (
    user_id INT NOT NULL,
    tag_id INT NOT NULL,

    PRIMARY KEY (user_id, tag_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    INDEX idx_user_tags_tag_id (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Record of digest emails sent to users (for dedupe/history)
CREATE TABLE IF NOT EXISTS digests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    content_ids TEXT,
    delivery_method VARCHAR(50) NOT NULL DEFAULT 'email',
    sent_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_digests_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- User-submitted feedback/support messages (submitter may be anonymous)
CREATE TABLE IF NOT EXISTS feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT DEFAULT NULL,
    email VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    feedback_type VARCHAR(50) NOT NULL DEFAULT 'general',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_feedback_status (status),
    INDEX idx_feedback_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Emails that unsubscribed/bounced and must never receive digests
CREATE TABLE IF NOT EXISTS email_blocklist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    reason VARCHAR(255) DEFAULT NULL,
    blocked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE INDEX idx_email_blocklist_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Email verification codes (e.g. sign-up confirmation)
-- NOTE: inferred table. Current api/routes only DELETE FROM verification_codes
-- (account deletion cleanup in auth.php/admin.php); no route in this codebase
-- reads or inserts into it. The frontend (frontend/src/lib/api.ts) calls
-- /api/auth/verify-email and /api/auth/resend-verification, but those routes
-- do not exist in api/routes/auth.php - this looks like drift from the
-- deleted Flask backend. Columns below mirror the password_reset_tokens
-- shape (short code instead of selector/verifier) as a best guess; verify
-- against production before trusting.
CREATE TABLE IF NOT EXISTS verification_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    code VARCHAR(10) NOT NULL,
    expires_at DATETIME NOT NULL,
    used_at DATETIME DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_verification_codes_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
