<?php
$jobDir = "/share/jobs/";
$results = glob($jobDir . "*.json");

echo "<h2>任務管理中心</h2>";
echo "<table border='1'><tr><th>任務ID</th><th>狀態</th><th>節點</th><th>操作</th></tr>";

foreach ($results as $metaFile) {
    $meta = json_decode(file_get_contents($metaFile), true);
    $statusText = $meta['status']; // 已經是中文狀態
    echo "<tr><td>{$meta['jobId']}</td><td>$statusText</td><td>{$meta['assigned_node']}</td><td>";
    if ($meta['status'] === '排隊中') {
        echo "<form method='post'><input type='hidden' name='delete' value='{$meta['jobId']}'><input type='submit' value='刪除'></form>";
    }
    echo "</td></tr>";
}
echo "</table>";

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['delete'])) {
    $jobId = $_POST['delete'];
    unlink($jobDir . $jobId . ".txt");
    unlink($jobDir . $jobId . ".json");
    echo "✅ 已刪除任務 $jobId<br>";
}

echo "<h3>節點資源狀態</h3>";
$nodes = ["computingNode1", "computingNode2", "computingNode3"];
foreach ($nodes as $node) {
    $statusFile = "/share/status/{$node}_status.txt";
    echo "<strong>$node:</strong><br>";
    if (file_exists($statusFile)) {
        echo "<pre>" . htmlspecialchars(file_get_contents($statusFile)) . "</pre>";
    } else {
        echo "⚠️ 無法讀取狀態資訊<br>";
    }
}
?>

<script>
setTimeout(() => {
  location.reload();
}, 2000); // 每 2 秒自動刷新一次頁面
</script>
