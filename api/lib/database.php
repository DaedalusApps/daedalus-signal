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
            $host = getenv('DB_HOST') ?: 'mysql.signal.daedalusapps.com';
            $name = getenv('DB_NAME') ?: 'daedalussignal';
            $user = getenv('DB_USER') ?: 'signal_db';
            $pass = getenv('DB_PASSWORD') ?: '';

            self::$pdo = new PDO(
                "mysql:host={$host};dbname={$name};charset=utf8mb4",
                $user,
                $pass,
                [
                    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                    PDO::ATTR_EMULATE_PREPARES => false
                ]
            );
        }
        return self::$pdo;
    }
}
