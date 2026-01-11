<?php
/**
 * Simple PSR-4 Autoloader for Firebase\JWT
 * No Composer required
 */

spl_autoload_register(function ($class) {
    // Firebase\JWT namespace
    $prefix = 'Firebase\\JWT\\';
    $base_dir = __DIR__ . '/firebase/php-jwt/src/';

    // Check if class uses the namespace prefix
    $len = strlen($prefix);
    if (strncmp($prefix, $class, $len) !== 0) {
        return;
    }

    // Get the relative class name
    $relative_class = substr($class, $len);

    // Replace namespace separators with directory separators
    $file = $base_dir . str_replace('\\', '/', $relative_class) . '.php';

    // If the file exists, require it
    if (file_exists($file)) {
        require $file;
    }
});
