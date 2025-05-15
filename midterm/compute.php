<?php
$node = "computingNode1"; // 手動指定節點名稱（依據節點自行修改）

echo "目前節點：$node\n";

$jobDir = "/share/jobs/";
$resultDir = "/share/results/";
$jobs = glob($jobDir . "*.json");

foreach ($jobs as $metaFile) {
    echo "讀取任務檔：$metaFile\n";
    $meta = json_decode(file_get_contents($metaFile), true);
    echo "任務 ID：{$meta['jobId']}\n";
    echo "狀態：{$meta['status']} | 指派節點：{$meta['assigned_node']}\n";

    if ($meta['status'] === 'queued' && $meta['assigned_node'] === $node) {
        echo "✅ 進入處理任務 {$meta['jobId']}\n";

        // 將狀態更新為 working
        $meta['status'] = 'working';
        file_put_contents($metaFile, json_encode($meta, JSON_UNESCAPED_UNICODE));

        $filepath = $jobDir . $meta['filename'];
        if (!file_exists($filepath)) {
            echo "❌ 找不到檔案：$filepath\n";
            continue;
        }

        $text = file_get_contents($filepath);
        $result = "任務由 $node 執行\n";

        foreach ($meta['keywords'] as $keyword) {
            $count = substr_count($text, $keyword);
            $result .= "🔍 關鍵字「$keyword」出現次數：$count\n";
        }

        file_put_contents($resultDir . $meta['jobId'] . ".txt", $result);

        // 最後將狀態更新為 done
        $meta['status'] = 'done';
        file_put_contents($metaFile, json_encode($meta, JSON_UNESCAPED_UNICODE));
        echo "✅ 任務完成，結果已寫入。\n";
        break;
    } else {
        echo "➡️ 跳過此任務（非此節點或狀態非 queued）\n";
    }
}
?>
