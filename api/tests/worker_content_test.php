<?php
/**
 * Standalone repro tests for two P1.7 bugs confirmed during the P1.3
 * schema review:
 *
 *   A. api/routes/worker.php:165-166 truncates title/description with
 *      byte-oriented substr(), which can split a multi-byte UTF-8
 *      character in half and produce an invalid UTF-8 string when the
 *      cut point lands mid-character.
 *
 *   B. api/routes/content.php (handle_get_new_count, "Parse ISO
 *      timestamp") turns a client-supplied `since` value into a
 *      `+00:00`-offset string via str_replace('Z', '+00:00', ...) and
 *      binds that directly into a `scraped_at > ?` comparison against a
 *      DATETIME column. MariaDB does not understand the offset suffix
 *      on a DATETIME comparison and truncates/warns (1292), so the
 *      value bound to SQL must be UTC-normalized and formatted as
 *      'Y-m-d H:i:s' with no offset.
 *
 * Both tests extract the *actual* source text from the route files
 * (same technique as api/tests/hardfail_test.php) and execute it in an
 * isolated subprocess, rather than reimplementing the logic, so a fix
 * in the real file is what makes the test go green.
 *
 * Run: php api/tests/worker_content_test.php
 * Exits 0 if both checks pass, nonzero otherwise.
 */

define('PHP_BIN', getenv('HARDFAIL_PHP_BIN') ?: PHP_BINARY);
define('API_DIR', dirname(__DIR__));

/**
 * Build the command array for a child PHP process. Some code under
 * test (the mb_substr fix) needs the mbstring extension. Most PHP
 * builds (including DreamHost's) have it enabled by default, but this
 * dev build does not, so if a first attempt fails with "undefined
 * function mb_*" the caller retries with explicit -d extension flags
 * pointing at the sibling ext/ directory of PHP_BIN.
 */
function child_command(string $tmp, bool $withMbstringFlags): array
{
    if (!$withMbstringFlags) {
        return [PHP_BIN, $tmp];
    }
    $extDir = dirname(PHP_BIN) . DIRECTORY_SEPARATOR . 'ext';
    return [
        PHP_BIN,
        '-d', 'extension_dir=' . $extDir,
        '-d', 'extension=mbstring',
        '-d', 'extension=pdo_mysql',
        $tmp,
    ];
}

/**
 * Run PHP code in an isolated subprocess (no DB/network required by
 * either code path under test).
 *
 * @return array{0:int,1:string,2:string} [exitCode, stdout, stderr]
 */
function run_php_code(string $phpCode, int $timeoutSeconds = 8): array
{
    $tmp = tempnam(sys_get_temp_dir(), 'wct_') . '.php';
    file_put_contents($tmp, $phpCode);

    [$exit, $out, $err] = run_php_command(child_command($tmp, false), $timeoutSeconds);
    if (stripos($out . $err, 'undefined function mb_') !== false) {
        [$exit, $out, $err] = run_php_command(child_command($tmp, true), $timeoutSeconds);
    }

    @unlink($tmp);

    return [$exit, $out, $err];
}

function run_php_command(array $command, int $timeoutSeconds): array
{
    $descriptors = [
        0 => ['pipe', 'r'],
        1 => ['pipe', 'w'],
        2 => ['pipe', 'w'],
    ];

    $process = proc_open($command, $descriptors, $pipes, API_DIR, null);
    if (!is_resource($process)) {
        return [-1, '', 'failed to start process'];
    }

    fclose($pipes[0]);
    stream_set_blocking($pipes[1], false);
    stream_set_blocking($pipes[2], false);

    $stdout = '';
    $stderr = '';
    $start = microtime(true);

    while (true) {
        $stdout .= stream_get_contents($pipes[1]);
        $stderr .= stream_get_contents($pipes[2]);

        $status = proc_get_status($process);
        if (!$status['running']) {
            break;
        }
        if ((microtime(true) - $start) > $timeoutSeconds) {
            proc_terminate($process, 9);
            break;
        }
        usleep(20000);
    }

    $stdout .= stream_get_contents($pipes[1]);
    $stderr .= stream_get_contents($pipes[2]);
    fclose($pipes[1]);
    fclose($pipes[2]);
    $exitCode = proc_close($process);

    return [$exitCode, $stdout, $stderr];
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
// Test A: worker.php:165-166 byte-truncation must not split a
// multi-byte UTF-8 character.
// ---------------------------------------------------------------------
$workerSource = file_get_contents(API_DIR . '/routes/worker.php');
$testName = 'worker.php title/description truncation produces valid UTF-8';

// Locate the truncation expressions structurally, independent of which
// function (substr vs mb_substr) is actually used: find the INSERT INTO
// contents statement, then the next $stmt->execute([ ... ]) array literal
// after it - that array's first two elements are the title/description
// truncation expressions under test.
$insertMarker = 'INSERT INTO contents';
$insertPos = strpos($workerSource, $insertMarker);
$execMarker = '$stmt->execute([';
$execStart = $insertPos === false ? false : strpos($workerSource, $execMarker, $insertPos);

if ($execStart === false) {
    record($testName, false, 'could not locate the $stmt->execute([ block following INSERT INTO contents in worker.php');
} else {
    $arrayStart = $execStart + strlen('$stmt->execute(');
    $closeMarker = ']);';
    $arrayEnd = strpos($workerSource, $closeMarker, $arrayStart);
    if ($arrayEnd === false) {
        record($testName, false, 'could not locate closing ]); after $stmt->execute(');
    } else {
        // Includes the outer [ ... ] of the array literal passed to execute().
        $arrayLiteral = substr($workerSource, $arrayStart, $arrayEnd + 1 - $arrayStart);

        // Title crafted so that byte 500 lands in the middle of the
        // trailing emoji's multi-byte UTF-8 encoding.
        $title = str_repeat('x', 498) . '🤖🚀🎉🔥💥';
        $description = str_repeat('y', 1998) . '🤖🚀🎉🔥💥';

        $itemVar = var_export([
            'title' => $title,
            'description' => $description,
            'content_type' => 'article',
        ], true);

        // The child emits exactly one marker-prefixed JSON line, so any
        // stray PHP warning/notice written to stdout (e.g. an undefined
        // array key) cannot be mistaken for the result: only a line that
        // starts with the marker and parses as strict JSON counts.
        $marker = 'WCT_RESULT_A:';
        $code = "<?php\n"
            . "\$item = {$itemVar};\n"
            . "\$url = 'https://example.com/x';\n"
            . "\$source_id = 1;\n"
            . "\$relevance_score = 50;\n"
            . "\$published_at = null;\n"
            . "\$test_array = {$arrayLiteral};\n"
            . "fwrite(STDOUT, " . var_export($marker, true) . " . json_encode([\n"
            . "    'title' => base64_encode(\$test_array[0]),\n"
            . "    'desc' => base64_encode(\$test_array[1]),\n"
            . "]) . \"\\n\");\n";

        [$exit, $out, $err] = run_php_code($code);

        $resultLine = null;
        foreach (explode("\n", $out) as $line) {
            if (str_starts_with($line, $marker)) {
                $resultLine = substr($line, strlen($marker));
                break;
            }
        }

        if ($resultLine === null) {
            record($testName, false, 'extraction/execution error: no ' . $marker . ' line in output: ' . substr($out . $err, 0, 300));
        } else {
            $decoded = json_decode($resultLine, true);
            if (json_last_error() !== JSON_ERROR_NONE || !is_array($decoded) || !isset($decoded['title']) || !isset($decoded['desc'])) {
                record($testName, false, 'extraction/execution error: malformed result JSON: ' . substr($resultLine, 0, 300));
            } else {
                $titleOut = base64_decode($decoded['title'], true);
                $descOut = base64_decode($decoded['desc'], true);
                $pass = $titleOut !== false && $descOut !== false
                    && mb_check_encoding($titleOut, 'UTF-8') && mb_check_encoding($descOut, 'UTF-8');
                record(
                    $testName,
                    $pass,
                    $pass ? '' : 'truncated title/description is NOT valid UTF-8 (byte-oriented substr split a multi-byte character)'
                );
            }
        }
    }
}

// ---------------------------------------------------------------------
// Test B: content.php "Parse ISO timestamp" must bind an offset-free,
// UTC-normalized 'Y-m-d H:i:s' value, not a raw +00:00-offset string.
// ---------------------------------------------------------------------
$contentSource = file_get_contents(API_DIR . '/routes/content.php');

$startMarker = '// Parse ISO timestamp';
$endMarker = '$db = Database::getConnection();';
$startPos = strpos($contentSource, $startMarker);
$endPos = $startPos === false ? false : strpos($contentSource, $endMarker, $startPos);

if ($startPos === false || $endPos === false) {
    record('content.php since-parsing binds UTC offset-free datetime', false, 'could not locate the since-parsing block in content.php');
} else {
    $sinceBlock = substr($contentSource, $startPos, $endPos - $startPos);
    $responsePath = var_export(API_DIR . '/lib/response.php', true);

    // A timestamp as the client would actually send it (Z-suffixed ISO 8601).
    $since = '2026-07-31T10:15:30Z';

    $code = "<?php\n"
        . "require {$responsePath};\n"
        . "\$since = " . var_export($since, true) . ";\n"
        . "{$sinceBlock}\n"
        . "fwrite(STDOUT, 'RESULT:' . (\$since_dt ?? 'NULL'));\n";

    [$exit, $out, $err] = run_php_code($code);
    $combined = trim($out . $err);

    if (!str_starts_with($combined, 'RESULT:')) {
        // The code under test may have called error_response() (exit),
        // or errored out some other way.
        record('content.php since-parsing binds UTC offset-free datetime', false, "did not produce a since_dt value: " . substr($combined, 0, 300));
    } else {
        $sinceDt = substr($combined, strlen('RESULT:'));
        $pass = (bool) preg_match('/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/', $sinceDt);
        record(
            'content.php since-parsing binds UTC offset-free datetime',
            $pass,
            $pass ? '' : "since_dt='{$sinceDt}' is not a bare UTC 'Y-m-d H:i:s' value (MariaDB warns/truncates on offset-suffixed DATETIME comparisons)"
        );
    }
}

// ---------------------------------------------------------------------
// Test C: content.php since-parsing must reject non-ISO-8601 `since`
// values (including PHP's own lenient DateTime-constructor formats like
// 'tomorrow' and '0000-00-00', which can yield a negative-year value
// bound into SQL) with a 400 error_response(), while still accepting the
// exact ISO-8601 shape the frontend's `Date.prototype.toISOString()`
// produces.
// ---------------------------------------------------------------------
if ($startPos === false || $endPos === false) {
    record('content.php since-parsing rejects invalid since with 400', false, 'could not locate the since-parsing block in content.php');
} else {
    $sinceBlock = substr($contentSource, $startPos, $endPos - $startPos);
    $responsePath = var_export(API_DIR . '/lib/response.php', true);

    $runSince = function (string $since) use ($sinceBlock, $responsePath): string {
        $code = "<?php\n"
            . "require {$responsePath};\n"
            . "register_shutdown_function(function () { fwrite(STDOUT, '|STATUS:' . http_response_code()); });\n"
            . "\$since = " . var_export($since, true) . ";\n"
            . "{$sinceBlock}\n"
            . "fwrite(STDOUT, 'RESULT:' . (\$since_dt ?? 'NULL'));\n";

        [$exit, $out, $err] = run_php_code($code);
        return trim($out . $err);
    };

    $rejectionCases = [
        'not-a-date' => 'not-a-date',
        "PHP DateTime-relative 'tomorrow'" => 'tomorrow',
        "PHP DateTime-relative 'now'" => 'now',
        "PHP DateTime timestamp '@0'" => '@0',
        "zero date '0000-00-00'" => '0000-00-00',
    ];

    foreach ($rejectionCases as $label => $since) {
        $combined = $runSince($since);
        $pass = !str_contains($combined, 'RESULT:')
            && str_contains($combined, 'STATUS:400')
            && str_contains($combined, '"error"');
        record(
            "content.php since-parsing rejects $label with 400",
            $pass,
            $pass ? '' : "expected a 400 error_response() and no since_dt binding, got: " . substr($combined, 0, 300)
        );
    }

    // Happy path: the exact shape produced by the frontend's
    // Date.prototype.toISOString() (millisecond-precision, Z-suffixed)
    // must still be accepted.
    $happySince = '2026-07-31T10:15:30.123Z';
    $combined = $runSince($happySince);
    if (!str_starts_with($combined, 'RESULT:')) {
        record(
            "content.php since-parsing accepts toISOString() shape ('$happySince')",
            false,
            "expected a since_dt value, got: " . substr($combined, 0, 300)
        );
    } else {
        $sinceDt = explode('|', substr($combined, strlen('RESULT:')), 2)[0];
        $pass = $sinceDt === '2026-07-31 10:15:30';
        record(
            "content.php since-parsing accepts toISOString() shape ('$happySince')",
            $pass,
            $pass ? '' : "expected since_dt='2026-07-31 10:15:30', got '$sinceDt'"
        );
    }
}

// ---------------------------------------------------------------------
$failures = count(array_filter($results, fn($p) => !$p));
echo "\n";
echo $failures === 0
    ? "ALL CHECKS PASSED (" . count($results) . "/" . count($results) . ")\n"
    : "$failures/" . count($results) . " CHECK(S) FAILED\n";

exit($failures === 0 ? 0 : 1);
