<?php
/**
 * Crow Pulsing Bridge (Gentle Extraction)
 */
ignore_user_abort(true);
set_time_limit(30);

$key = "{{KEY}}";
$packFile = "{{ZIP_NAME}}";
$targetDir = __DIR__;
$bridgeFile = __FILE__;

if (($_POST['key'] ?? '') !== $key) {
    header('HTTP/1.1 403 Forbidden');
    exit;
}

$pointer = (int)($_POST['pointer'] ?? 0);
$startTime = time();
$report = ['extracted' => 0, 'errors' => [], 'done' => false, 'next_pointer' => 0];

try {
    if (!file_exists($packFile)) {
        throw new Exception("Pack file not found: $packFile");
    }

    $handle = fopen($packFile, "rb");
    fseek($handle, $pointer);

    while (!feof($handle)) {
        // Pulse: 5 seconds only to be very safe
        if (time() - $startTime > 5) {
            $report['next_pointer'] = ftell($handle);
            $report['done'] = false;
            echo json_encode($report);
            fclose($handle);
            exit;
        }

        $pathLenData = fread($handle, 4);
        if (strlen($pathLenData) < 4) break;
        
        $pathLen = unpack("N", $pathLenData)[1];
        $path = fread($handle, $pathLen);
        
        $dataLenData = fread($handle, 8);
        if (strlen($dataLenData) < 8) break;
        $dataLen = unpack("J", $dataLenData)[1];
        
        $fullPath = $targetDir . DIRECTORY_SEPARATOR . $path;
        $parentDir = dirname($fullPath);
        
        if (!is_dir($parentDir)) {
            mkdir($parentDir, 0755, true);
        }

        $outHandle = fopen($fullPath, "wb");
        if ($outHandle) {
            $remaining = $dataLen;
            while ($remaining > 0) {
                $chunkSize = min($remaining, 65536);
                $chunk = fread($handle, $chunkSize);
                fwrite($outHandle, $chunk);
                $remaining -= strlen($chunk);
                // Tiny sleep to lower IO pressure
                usleep(5000); 
            }
            fclose($outHandle);
            $report['extracted']++;
        } else {
            fseek($handle, $dataLen, SEEK_CUR);
            $report['errors'][] = "Failed to write: $path";
        }
    }
    
    fclose($handle);
    $report['done'] = true;
    $report['success'] = true;
    @unlink($packFile);
    @unlink($bridgeFile);

} catch (Exception $e) {
    $report['success'] = false;
    $report['errors'][] = $e->getMessage();
}

header('Content-Type: application/json');
echo json_encode($report);
