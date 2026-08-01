<?php
/**
 * Database Seeder for DaedalusSignal
 *
 * Run from command line:
 *   php seed.php
 *
 * Or via browser (if hosted):
 *   https://signal.daedalusapps.com/api/seed.php?key=YOUR_SECRET_KEY
 *
 * Environment variables (set in .htaccess or export before running):
 *   DB_HOST, DB_NAME, DB_USER, DB_PASSWORD
 *   ADMIN_EMAIL, ADMIN_PASSWORD
 *   SEED_KEY (optional, for web access protection)
 */

// Protect web access with a secret key
if (php_sapi_name() !== 'cli') {
    $seedKey = getenv('SEED_KEY') ?: '';
    $providedKey = $_GET['key'] ?? '';

    if (empty($seedKey) || $providedKey !== $seedKey) {
        http_response_code(403);
        die(json_encode(['error' => 'Forbidden - invalid or missing seed key']));
    }
    header('Content-Type: application/json');
}

require_once __DIR__ . '/lib/database.php';

// Configuration
$adminEmail = getenv('ADMIN_EMAIL') ?: '';
$adminPassword = getenv('ADMIN_PASSWORD') ?: '';

if (!$adminEmail || !$adminPassword) {
    $error = 'ADMIN_EMAIL and ADMIN_PASSWORD environment variables must be set';
    output($error);
    if (php_sapi_name() !== 'cli') {
        http_response_code(500);
        echo json_encode(['error' => $error]);
    }
    exit(1);
}

// Default sources from defaults.md
$defaultSources = [
    // X (Twitter) - ordered by external influence
    ['name' => '@karpathy', 'url' => 'https://x.com/karpathy', 'source_type' => 'twitter'],
    ['name' => '@AnthropicAI', 'url' => 'https://x.com/AnthropicAI', 'source_type' => 'twitter'],
    ['name' => '@MistralAI', 'url' => 'https://x.com/MistralAI', 'source_type' => 'twitter'],
    ['name' => '@cursor_ai', 'url' => 'https://x.com/cursor_ai', 'source_type' => 'twitter'],
    ['name' => '@Steve_Yegge', 'url' => 'https://x.com/Steve_Yegge', 'source_type' => 'twitter'],
    ['name' => '@emollick', 'url' => 'https://x.com/emollick', 'source_type' => 'twitter'],
    ['name' => '@bcherny', 'url' => 'https://x.com/bcherny', 'source_type' => 'twitter'],
    ['name' => '@langchain_oss', 'url' => 'https://x.com/LangChainAI', 'source_type' => 'twitter'],
    ['name' => '@GroqInc', 'url' => 'https://x.com/GroqInc', 'source_type' => 'twitter'],
    ['name' => '@manusai', 'url' => 'https://x.com/manaboroshii', 'source_type' => 'twitter'],

    // YouTube - channels for the same accounts
    ['name' => 'Andrej Karpathy', 'url' => 'https://www.youtube.com/c/AndrejKarpathy', 'source_type' => 'youtube'],
    ['name' => 'Anthropic', 'url' => 'https://www.youtube.com/@anthropic-ai', 'source_type' => 'youtube'],
    ['name' => 'Mistral AI', 'url' => 'https://www.youtube.com/@MistralAIOfficial', 'source_type' => 'youtube'],
    ['name' => 'Cursor', 'url' => 'https://www.youtube.com/@cursor_ai', 'source_type' => 'youtube'],
    ['name' => 'Steve Yegge', 'url' => 'https://www.youtube.com/steveyegge', 'source_type' => 'youtube'],
    ['name' => 'LangChain', 'url' => 'https://www.youtube.com/@LangChain', 'source_type' => 'youtube'],
    ['name' => 'Groq', 'url' => 'https://www.youtube.com/c/GroqInc', 'source_type' => 'youtube'],
    ['name' => 'Manus AI', 'url' => 'https://www.youtube.com/@Manus-AI', 'source_type' => 'youtube'],
];

// Default tags from defaults.md - ordered by external popularity
$defaultTags = [
    ['name' => 'AI', 'category' => 'general'],
    ['name' => 'ArtificialIntelligence', 'category' => 'general'],
    ['name' => 'MachineLearning', 'category' => 'general'],
    ['name' => 'DeepLearning', 'category' => 'general'],
    ['name' => 'Tech', 'category' => 'general'],
    ['name' => 'DataScience', 'category' => 'general'],
    ['name' => 'Robotics', 'category' => 'general'],
    ['name' => 'Coding', 'category' => 'tools'],
    ['name' => 'Python', 'category' => 'tools'],
    ['name' => 'Innovation', 'category' => 'general'],
    ['name' => 'Startup', 'category' => 'general'],
    ['name' => 'BigData', 'category' => 'general'],
    ['name' => 'CloudComputing', 'category' => 'tools'],
    ['name' => 'Programming', 'category' => 'tools'],
    ['name' => 'Developer', 'category' => 'tools'],
    ['name' => 'Analytics', 'category' => 'general'],
    ['name' => 'DigitalTransformation', 'category' => 'general'],
    ['name' => 'Automation', 'category' => 'tools'],
    ['name' => 'Computerscience', 'category' => 'general'],
    ['name' => 'Blockchain', 'category' => 'general'],
    ['name' => 'IoT', 'category' => 'general'],
];

function output($message) {
    if (php_sapi_name() === 'cli') {
        echo $message . "\n";
    }
}

function seedAdminUser($pdo, $email, $password) {
    output("Seeding admin user...");

    // Check if admin exists
    $stmt = $pdo->prepare("SELECT id FROM users WHERE email = ?");
    $stmt->execute([$email]);

    if ($stmt->fetch()) {
        output("  Admin user already exists: $email");
        return;
    }

    // Create admin user
    $passwordHash = password_hash($password, PASSWORD_BCRYPT, ['cost' => 12]);

    $stmt = $pdo->prepare("
        INSERT INTO users (email, password_hash, is_admin, is_active, onboarding_complete, created_at, updated_at)
        VALUES (?, ?, 1, 1, 1, NOW(), NOW())
    ");
    $stmt->execute([$email, $passwordHash]);

    output("  Created admin user: $email");
}

function seedDefaultSources($pdo, $sources) {
    output("Seeding default sources...");

    $stmt = $pdo->prepare("SELECT url FROM sources WHERE url = ?");
    $insertStmt = $pdo->prepare("
        INSERT INTO sources (name, url, source_type, is_default, is_approved, created_at, updated_at)
        VALUES (?, ?, ?, 1, 1, NOW(), NOW())
    ");

    foreach ($sources as $src) {
        $stmt->execute([$src['url']]);
        if (!$stmt->fetch()) {
            $insertStmt->execute([$src['name'], $src['url'], $src['source_type']]);
            output("  Added source: {$src['name']}");
        }
    }
}

function seedDefaultTags($pdo, $tags) {
    output("Seeding default tags...");

    $stmt = $pdo->prepare("SELECT name FROM tags WHERE name = ?");
    $insertStmt = $pdo->prepare("
        INSERT INTO tags (name, category, is_default, created_at, updated_at)
        VALUES (?, ?, 1, NOW(), NOW())
    ");

    foreach ($tags as $tag) {
        $stmt->execute([$tag['name']]);
        if (!$stmt->fetch()) {
            $insertStmt->execute([$tag['name'], $tag['category']]);
            output("  Added tag: {$tag['name']}");
        }
    }
}

function cleanupDisabledSources($pdo) {
    output("Cleaning up disabled sources (GitHub/LinkedIn)...");

    // Remove user associations first
    $pdo->exec("
        DELETE us FROM user_sources us
        JOIN sources s ON us.source_id = s.id
        WHERE s.source_type IN ('github', 'linkedin')
    ");

    // Remove the sources
    $stmt = $pdo->prepare("DELETE FROM sources WHERE source_type IN ('github', 'linkedin')");
    $stmt->execute();
    $count = $stmt->rowCount();

    if ($count > 0) {
        output("  Removed $count disabled source(s)");
    } else {
        output("  No disabled sources to remove");
    }
}

// Main execution
try {
    $pdo = Database::getConnection();

    output("DaedalusSignal Database Seeder");
    output("==============================");
    output("");

    cleanupDisabledSources($pdo);
    output("");

    seedAdminUser($pdo, $adminEmail, $adminPassword);
    output("");

    seedDefaultSources($pdo, $defaultSources);
    output("");

    seedDefaultTags($pdo, $defaultTags);
    output("");

    output("Database seeded successfully!");

    if (php_sapi_name() !== 'cli') {
        echo json_encode(['success' => true, 'message' => 'Database seeded successfully']);
    }

} catch (PDOException $e) {
    $error = "Database error: " . $e->getMessage();
    output($error);

    if (php_sapi_name() !== 'cli') {
        http_response_code(500);
        echo json_encode(['error' => $error]);
    }
    exit(1);
}
