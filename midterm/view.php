<?php
if (!isset($_GET['jobId'])) {
    echo "請提供 jobId 參數";
    exit;
}
$jobId = $_GET['jobId'];
$resultFile = "/share/results/$jobId.txt";

if (file_exists($resultFile)) {
    echo nl2br(file_get_contents($resultFile));
} else {
    echo "任務尚未完成，請稍後再試。";
}
?>
