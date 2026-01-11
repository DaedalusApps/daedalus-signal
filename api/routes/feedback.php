<?php
/**
 * Feedback Routes
 * 
 * POST /api/feedback - Submit user feedback
 */

$uri = preg_replace('#^/api#', '', parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));
$method = $_SERVER['REQUEST_METHOD'];

if ($uri === '/feedback' && $method === 'POST') {
    handle_submit_feedback();
} else {
    error_response('Not found', 404);
}

/**
 * POST /api/feedback
 */
function handle_submit_feedback(): void
{
    $data = get_json_body();

    if (!$data || empty($data['email']) || empty($data['message'])) {
        error_response('Email and message required', 400);
    }

    // Get user ID if authenticated (optional)
    $user_id = get_user_from_request();

    $db = Database::getConnection();

    $stmt = $db->prepare("
        INSERT INTO feedback (user_id, email, message, feedback_type, status, created_at)
        VALUES (?, ?, ?, ?, 'pending', NOW())
    ");
    $stmt->execute([
        $user_id,
        $data['email'],
        $data['message'],
        $data['feedback_type'] ?? 'general'
    ]);

    json_response(['message' => 'Feedback submitted successfully'], 201);
}
