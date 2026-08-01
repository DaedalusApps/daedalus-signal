<?php
/**
 * Database Connection using PDO
 * All DB credentials should be in .htaccess as SetEnv variables
 */

class Database
{
    private static ?PDO $pdo = null;

    public static function getConnection(): PDO
    {
        if (self::$pdo === null) {
            $host = getenv('DB_HOST') ?: '';
            $name = getenv('DB_NAME') ?: '';
            $user = getenv('DB_USER') ?: '';
            $pass = getenv('DB_PASSWORD') ?: '';

            if (!$host || !$name || !$user) {
                throw new RuntimeException('DB_HOST, DB_NAME, and DB_USER environment variables must be set');
            }

            self::$pdo = new PDO(
                "mysql:host={$host};dbname={$name};charset=utf8mb4",
                $user,
                $pass,
                [
                    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                    PDO::ATTR_EMULATE_PREPARES => false,
                    PDO::MYSQL_ATTR_INIT_COMMAND => "SET time_zone = '+00:00'"
                ]
            );
        }
        return self::$pdo;
    }
}
