-- =========================================================
-- BlogSphere - Full-Stack Blog & Content Management Database
-- Target Database: MySQL 5.7+ / 8.0+ / MariaDB 10.3+
-- Compatible with XAMPP, WAMP, Docker, phpMyAdmin
-- =========================================================

CREATE DATABASE IF NOT EXISTS blogsphere
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE blogsphere;

-- ---------------------------------------------------------
-- 1. USERS TABLE
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(191) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
    profile_image VARCHAR(500) DEFAULT NULL,
    bio TEXT DEFAULT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    last_login DATETIME DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email),
    INDEX idx_users_role (role),
    INDEX idx_users_active (is_active)
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- 2. USER SETTINGS TABLE
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_settings (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL UNIQUE,
    theme ENUM('light', 'dark', 'system') NOT NULL DEFAULT 'light',
    email_notifications TINYINT(1) NOT NULL DEFAULT 1,
    comment_notifications TINYINT(1) NOT NULL DEFAULT 1,
    post_visibility ENUM('public', 'private') NOT NULL DEFAULT 'public',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_settings_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- 3. CATEGORIES TABLE
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(120) NOT NULL UNIQUE,
    description VARCHAR(500) DEFAULT NULL,
    created_by INT UNSIGNED DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_categories_creator
        FOREIGN KEY (created_by) REFERENCES users(id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_categories_slug (slug)
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- 4. POSTS TABLE
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS posts (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    author_id INT UNSIGNED NOT NULL,
    category_id INT UNSIGNED DEFAULT NULL,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    excerpt VARCHAR(1000) DEFAULT NULL,
    content LONGTEXT NOT NULL,
    featured_image VARCHAR(1000) DEFAULT NULL,
    status ENUM('draft', 'published', 'archived') NOT NULL DEFAULT 'draft',
    is_featured TINYINT(1) NOT NULL DEFAULT 0,
    views_count BIGINT UNSIGNED NOT NULL DEFAULT 0,
    reading_time_minutes INT UNSIGNED NOT NULL DEFAULT 1,
    published_at DATETIME DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_posts_author
        FOREIGN KEY (author_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_posts_category
        FOREIGN KEY (category_id) REFERENCES categories(id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_posts_author (author_id),
    INDEX idx_posts_category (category_id),
    INDEX idx_posts_status (status),
    INDEX idx_posts_published_at (published_at),
    INDEX idx_posts_featured (is_featured),
    INDEX idx_posts_created_at (created_at),
    INDEX idx_posts_slug (slug),
    INDEX idx_posts_status_date (status, published_at)
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- 5. TAGS TABLE
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS tags (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(120) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tags_slug (slug)
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- 6. POST_TAGS TABLE (Many-to-Many)
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS post_tags (
    post_id INT UNSIGNED NOT NULL,
    tag_id INT UNSIGNED NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (post_id, tag_id),
    CONSTRAINT fk_post_tags_post
        FOREIGN KEY (post_id) REFERENCES posts(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_post_tags_tag
        FOREIGN KEY (tag_id) REFERENCES tags(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_post_tags_tag (tag_id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- 7. COMMENTS TABLE
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS comments (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    post_id INT UNSIGNED NOT NULL,
    user_id INT UNSIGNED DEFAULT NULL,
    parent_comment_id BIGINT UNSIGNED DEFAULT NULL,
    guest_name VARCHAR(100) DEFAULT NULL,
    guest_email VARCHAR(191) DEFAULT NULL,
    content TEXT NOT NULL,
    status ENUM('pending', 'approved', 'rejected', 'spam') NOT NULL DEFAULT 'approved',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_comments_post
        FOREIGN KEY (post_id) REFERENCES posts(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_comments_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_comments_parent
        FOREIGN KEY (parent_comment_id) REFERENCES comments(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_comments_post (post_id),
    INDEX idx_comments_user (user_id),
    INDEX idx_comments_status (status),
    INDEX idx_comments_parent (parent_comment_id),
    INDEX idx_comments_created (created_at)
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- 8. POST_VIEWS TABLE
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS post_views (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    post_id INT UNSIGNED NOT NULL,
    user_id INT UNSIGNED DEFAULT NULL,
    visitor_identifier VARCHAR(191) DEFAULT NULL,
    ip_hash VARCHAR(255) DEFAULT NULL,
    user_agent VARCHAR(500) DEFAULT NULL,
    viewed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_post_views_post
        FOREIGN KEY (post_id) REFERENCES posts(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_post_views_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_post_views_post (post_id),
    INDEX idx_post_views_user (user_id),
    INDEX idx_post_views_date (viewed_at),
    INDEX idx_post_views_visitor (visitor_identifier)
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- SEED DEFAULT CATEGORIES
-- ---------------------------------------------------------
INSERT IGNORE INTO categories (name, slug, description) VALUES
('Technology', 'technology', 'Technology, software and emerging innovations.'),
('Artificial Intelligence', 'artificial-intelligence', 'AI, machine learning and generative artificial intelligence.'),
('Programming', 'programming', 'Programming languages, architectural concepts and software development.'),
('Web Development', 'web-development', 'Frontend, backend, modern web APIs, and full-stack development.'),
('Cybersecurity', 'cybersecurity', 'Cybersecurity defense, security practices, privacy and online safety.'),
('Tutorials', 'tutorials', 'Step-by-step technical guides, tutorials and practical walkthroughs.'),
('Productivity', 'productivity', 'Developer workflows, tooling, efficiency and productive habits.'),
('Business', 'business', 'Tech startups, digital enterprise and software business models.');

-- ---------------------------------------------------------
-- SEED DEFAULT TAGS
-- ---------------------------------------------------------
INSERT IGNORE INTO tags (name, slug) VALUES
('AI', 'ai'),
('Python', 'python'),
('FastAPI', 'fastapi'),
('JavaScript', 'javascript'),
('HTML', 'html'),
('CSS', 'css'),
('React', 'react'),
('MySQL', 'mysql'),
('Web Development', 'web-development'),
('Cybersecurity', 'cybersecurity'),
('Programming', 'programming'),
('Tutorial', 'tutorial'),
('Technology', 'technology');
