<?php
/**
 * Hard-fail harness for P1.1 Security hardening.
 *
 * Verifies, by spawning isolated `php` subprocesses with a scrubbed
 * environment, that the following paths FAIL CLOSED when their required
 * secret/config environment variables are missing (instead of silently
 * falling back to an insecure default):
 *
 *   1. api/seed.php                       - ADMIN_EMAIL / ADMIN_PASSWORD
 *   2. api/lib/database.php               - DB_HOST / DB_NAME / DB_USER
 *   3. api/lib/auth.php verify_turnstile() - TURNSTILE_SECRET_KEY
 *   4. api/lib/jwt.php                    - JWT_SECRET
 *   5. api/routes/unsubscribe.php HMAC    - SECRET_KEY
 *
 * No real database or network access is required. Run from the CLI:
 *   php api/tests/hardfail_test.php
 *
 * Exits 0 if every path fails closed, nonzero if any path fails open.
 */

define('PHP_BIN', getenv('HARDFAIL_PHP_BIN') ?: PHP_BINARY);
define('API_DIR', dirname(__DIR__));

// Env vars that must be unset in every isolated subprocess for these checks
// to be meaningful.
const SCRUB_VARS = [
    'ADMIN_EMAIL',
    'ADMIN_PASSWORD',
    'DB_HOST',
    'DB_NAME',
    'DB_USER',
    'DB_PASSWORD',
    'TURNSTILE_SECRET_KEY',
    'JWT_SECRET',
    'SECRET_KEY', // unsubscribe HMAC secret
];

/**
 * Build the environment for a child process: inherit the current
 * environment, then strip every secret this harness cares about.
 */
function scrubbed_env(): array
{
    $env = [];
    foreach ($_SERVER as $k => $v) {
        if (is_string($v)) {
            $env[$k] = $v;
        }
    }
    foreach (getenv() as $k => $v) {
        $env[$k] = $v;
    }
    foreach (SCRUB_VARS as $k) {
        unset($env[$k]);
    }
    return $env;
}

/**
 * Run a PHP file in an isolated subprocess with the scrubbed environment,
 * killing it if it runs longer than $timeoutSeconds.
 *
 * @return array{0:int,1:string,2:string,3:bool} [exitCode, stdout, stderr, timedOut]
 */
function run_php_file(string $scriptPath, int $timeoutSeconds = 8): array
{
    $descriptors = [
        0 => ['pipe', 'r'],
        1 => ['pipe', 'w'],
        2 => ['pipe', 'w'],
    ];

    $process = proc_open([PHP_BIN, $scriptPath], $descriptors, $pipes, API_DIR, scrubbed_env());

    if (!is_resource($process)) {
        return [-1, '', 'failed to start process', false];
    }

    fclose($pipes[0]);
    stream_set_blocking($pipes[1], false);
    stream_set_blocking($pipes[2], false);

    $stdout = '';
    $stderr = '';
    $start = microtime(true);
    $timedOut = false;

    while (true) {
        $stdout .= stream_get_contents($pipes[1]);
        $stderr .= stream_get_contents($pipes[2]);

        $status = proc_get_status($process);
        if (!$status['running']) {
            break;
        }

        if ((microtime(true) - $start) > $timeoutSeconds) {
            $timedOut = true;
            proc_terminate($process, 9);
            break;
        }

        usleep(50000);
    }

    $stdout .= stream_get_contents($pipes[1]);
    $stderr .= stream_get_contents($pipes[2]);
    fclose($pipes[1]);
    fclose($pipes[2]);
    $exitCode = proc_close($process);

    return [$timedOut ? -1 : $exitCode, $stdout, $stderr, $timedOut];
}

/**
 * Write $phpCode to a temp file and run it via run_php_file().
 */
function run_php_code(string $phpCode, int $timeoutSeconds = 8): array
{
    $tmp = tempnam(sys_get_temp_dir(), 'hardfail_') . '.php';
    file_put_contents($tmp, $phpCode);
    try {
        return run_php_file($tmp, $timeoutSeconds);
    } finally {
        @unlink($tmp);
    }
}

$results = [];

function record(string $name, bool $pass, string $detail): void
{
    global $results;
    $results[] = $pass;
    $status = $pass ? 'PASS' : 'FAIL';
    echo "[$status] $name\n";
    if ($detail !== '') {
        echo "        $detail\n";
    }
}

// ---------------------------------------------------------------------
// 1. api/seed.php must refuse to run without ADMIN_EMAIL/ADMIN_PASSWORD.
// ---------------------------------------------------------------------
[$exit, $out, $err, $timedOut] = run_php_file(API_DIR . '/seed.php');
$combined = $out . $err;
$mentionsAdmin = stripos($combined, 'ADMIN_EMAIL') !== false && stripos($combined, 'ADMIN_PASSWORD') !== false;
$pass = !$timedOut && $exit !== 0 && $mentionsAdmin;
record(
    'seed.php refuses to run without ADMIN_EMAIL/ADMIN_PASSWORD',
    $pass,
    $timedOut
        ? 'TIMED OUT (still attempting to run with default/fallback credentials)'
        : "exit={$exit} output=" . trim(substr($combined, 0, 200))
);

// ---------------------------------------------------------------------
// 2. api/lib/database.php must hard-fail without DB_HOST/DB_NAME/DB_USER,
//    instead of connecting with hardcoded defaults.
// ---------------------------------------------------------------------
$dbPath = var_export(API_DIR . '/lib/database.php', true);
$code = <<<PHP
<?php
require {$dbPath};
try {
    Database::getConnection();
    echo 'NO_EXCEPTION';
} catch (Throwable \$e) {
    echo get_class(\$e) . ':' . \$e->getMessage();
}
PHP;
[$exit, $out, $err, $timedOut] = run_php_code($code);
$combined = trim($out . $err);
$isConfigException = $combined !== '' && $combined !== 'NO_EXCEPTION' && stripos($combined, 'PDOException') === false;
$pass = !$timedOut && $isConfigException;
record(
    'database.php hard-fails without DB_HOST/DB_NAME/DB_USER',
    $pass,
    $timedOut
        ? 'TIMED OUT (attempted a real connection using default host)'
        : "output=" . substr($combined, 0, 200)
);

// ---------------------------------------------------------------------
// 3. auth.php verify_turnstile() must return false (or throw) without
//    TURNSTILE_SECRET_KEY, instead of returning true.
// ---------------------------------------------------------------------
$authPath = var_export(API_DIR . '/lib/auth.php', true);
$code = <<<PHP
<?php
require {$authPath};
try {
    var_export(verify_turnstile('some-token'));
} catch (Throwable \$e) {
    echo 'THROWN:' . get_class(\$e);
}
PHP;
[$exit, $out, $err, $timedOut] = run_php_code($code, 5);
$stdout = trim($out);
$pass = !$timedOut && ($stdout === 'false' || str_starts_with($stdout, 'THROWN:'));
record(
    'verify_turnstile() fails closed without TURNSTILE_SECRET_KEY',
    $pass,
    "output=" . substr(trim($out . $err), 0, 200)
);

// ---------------------------------------------------------------------
// 4. jwt.php must refuse to sign a token without JWT_SECRET.
// ---------------------------------------------------------------------
$jwtPath = var_export(API_DIR . '/lib/jwt.php', true);
$code = <<<PHP
<?php
try {
    require {$jwtPath};
    \$token = create_access_token(1, false);
    echo 'TOKEN:' . \$token;
} catch (Throwable \$e) {
    echo 'THROWN:' . get_class(\$e) . ':' . \$e->getMessage();
}
PHP;
[$exit, $out, $err, $timedOut] = run_php_code($code, 5);
$combined = trim($out . $err);
// Note: the firebase/php-jwt library itself throws an InvalidArgumentException
// if $key isn't a string, which incidentally aborts signing today - but that's
// an accident of the library's internal type-check, not an explicit app-level
// guard. Require the app's own RuntimeException so the check only passes once
// jwt.php validates JWT_SECRET itself, before ever calling encode()/decode().
$pass = !$timedOut && str_starts_with($combined, 'THROWN:RuntimeException:');
record(
    'jwt.php refuses to sign a token without JWT_SECRET',
    $pass,
    "output=" . substr($combined, 0, 200)
);

// ---------------------------------------------------------------------
// 5. unsubscribe.php HMAC must not fall back to '' when its secret env
//    var is unset. Tested via an include harness that pulls the real
//    generate_unsubscribe_token()/verify_unsubscribe_token() function
//    bodies out of the route file (which has request-dispatch side
//    effects at the top level that make it unsafe to `require` directly
//    in a CLI harness) without executing the routing/DB code.
// ---------------------------------------------------------------------
$unsubSource = file_get_contents(API_DIR . '/routes/unsubscribe.php');
$marker = 'function generate_unsubscribe_token';
$markerPos = strpos($unsubSource, $marker);
if ($markerPos === false) {
    record('unsubscribe.php HMAC fails closed without its secret', false, 'could not locate generate_unsubscribe_token() in source');
} else {
    $functionsSource = substr($unsubSource, $markerPos);
    $responsePath = var_export(API_DIR . '/lib/response.php', true);
    $code = "<?php\nrequire {$responsePath};\n{$functionsSource}\n"
        . "\$token = generate_unsubscribe_token('test@example.com');\n"
        . "echo 'TOKEN:' . \$token;\n";
    [$exit, $out, $err, $timedOut] = run_php_code($code, 5);
    $combined = trim($out . $err);
    // Fail-open behaviour computes and prints a real HMAC token.
    // Fail-closed behaviour must error out (e.g. via error_response(), a
    // 500 JSON body, or a thrown exception) before a token is printed.
    $pass = !$timedOut && !str_starts_with($combined, 'TOKEN:');
    record(
        'unsubscribe.php HMAC fails closed without its secret env var',
        $pass,
        "output=" . substr($combined, 0, 200)
    );
}

// ---------------------------------------------------------------------
$failures = count(array_filter($results, fn($p) => !$p));
echo "\n";
echo $failures === 0
    ? "ALL CHECKS PASSED (" . count($results) . "/" . count($results) . ")\n"
    : "$failures/" . count($results) . " CHECK(S) FAILED\n";

exit($failures === 0 ? 0 : 1);
