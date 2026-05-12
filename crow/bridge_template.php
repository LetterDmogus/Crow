<?php
/**
 * Crow Speed Bridge
 * One-time use script for ZIP extraction and Smart Clean.
 */

$key = "{{KEY}}";
$zipName = "{{ZIP_NAME}}";
$targetDir = __DIR__;

if (($_GET['key'] ?? '') !== $key) {
    header('HTTP/1.1 403 Forbidden');
    echo json_encode(['success' => false, 'error' => 'Invalid key']);
    exit;
}

$report = ['deleted' => [], 'extracted' => 0, 'errors' => []];

try {
    $zip = new ZipArchive;
    if ($zip->open($zipName) === TRUE) {
        // 1. Get list of files in ZIP
        $zipFiles = [];
        for ($i = 0; $i < $zip->numFiles; $i++) {
            $zipFiles[] = $zip->getNameIndex($i);
        }

        // 2. Smart Clean: Delete files in targetDir not in ZIP
        $iterator = new RecursiveIteratorIterator(
            new RecursiveDirectoryIterator($targetDir, RecursiveDirectoryIterator::SKIP_DOTS),
            RecursiveIteratorIterator::CHILD_FIRST
        );

        foreach ($iterator as $file) {
            $relativePath = str_replace($targetDir . DIRECTORY_SEPARATOR, '', $file->getRealPath());
            
            // Don't delete the bridge or the zip itself
            if ($relativePath === basename(__FILE__) || $relativePath === $zipName) continue;
            
            if (!in_array($relativePath, $zipFiles)) {
                if ($file->isDir()) {
                    @rmdir($file->getRealPath());
                } else {
                    @unlink($file->getRealPath());
                }
                $report['deleted'][] = $relativePath;
            }
        }

        // 3. Extract All
        $zip->extractTo($targetDir);
        $report['extracted'] = $zip->numFiles;
        $zip->close();
        
        $report['success'] = true;
    } else {
        throw new Exception("Failed to open ZIP file");
    }
} catch (Exception $e) {
    $report['success'] = false;
    $report['errors'][] = $e->getMessage();
}

// 4. Self Destruct
@unlink($zipName);
@unlink(__FILE__);

header('Content-Type: application/json');
echo json_encode($report);
