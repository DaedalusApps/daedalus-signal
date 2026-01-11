<?php
/**
 * JSON Response Helpers
 */

/**
 * Send a JSON response with status code
 */
function json_response(array $data, int $status = 200): void
{
    http_response_code($status);
    header('Content-Type: application/json');
    echo json_encode($data);
    exit;
}

/**
 * Send an error response
 */
function error_response(string $message, int $status = 400): void
{
    json_response(['error' => $message], $status);
}

/**
 * Get JSON body from request
 */
function get_json_body(): ?array
{
    $input = file_get_contents('php://input');
    if (empty($input)) {
        return null;
    }
    return json_decode($input, true);
}
