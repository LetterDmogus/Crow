<?php
header('Content-Type: application/json');
echo json_encode([
    'php_version' => PHP_VERSION,
    'zip_archive_exists' => class_exists('ZipArchive'),
    'exec_enabled' => function_exists('exec'),
    'loaded_extensions' => get_loaded_extensions(),
    'server_software' => $_SERVER['SERVER_SOFTWARE'] ?? 'unknown',
    'cwd' => getcwd()
], JSON_PRETTY_PRINT);
