<?php
$jobDir = "/share/jobs/";
$results = glob($jobDir . "*.json");

echo "<h2>任務管理</h2><table border='1'><tr><th>任務ID</th><th>狀態</th><th>節點</th><th>操作</th></tr>";

foreach ($results as $metaFile) {
    $meta = json_decode(file_get_contents($metaFile), true);
    echo "<tr>";
    echo "<td>{$meta['jobId']}</td>";
    echo "<td>{$meta['status']}</td>";
    echo "<td>{$meta['assigned_node']}</td>";
    echo "<td>";
    if ($meta['status'] === 'queued') {
        echo "<form method='post'><input type='hidden' name='delete' value='{$meta['jobId']}'><input type='submit' value='刪除'></form>";
    }
    echo "</td></tr>";
}
echo "</table>";

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['delete'])) {
    $jobId = $_POST['delete'];
    unlink($jobDir . $jobId . ".csv");
    unlink($jobDir . $jobId . ".json");
    echo "已刪除任務 $jobId<br>";
}
?>
