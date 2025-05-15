<?php
$node = gethostname();
$jobDir = "/share/jobs/";
$resultDir = "/share/results/";
$jobs = glob($jobDir . "*.json");

foreach ($jobs as $metaFile) {
    $meta = json_decode(file_get_contents($metaFile), true);
    if ($meta['status'] === 'queued' && $meta['assigned_node'] === $node) {
        $filepath = $jobDir . $meta['filename'];
        if (!file_exists($filepath)) continue;

        $text = file_get_contents($filepath);
        $result = "任務由 $node 執行\n";

        foreach ($meta['keywords'] as $keyword) {
            $count = substr_count($text, $keyword);
            $result .= "🔍 關鍵字「$keyword」出現次數：$count\n";
        }

        file_put_contents($resultDir . $meta['jobId'] . ".txt", $result);
        $meta['status'] = 'done';
        file_put_contents($metaFile, json_encode($meta, JSON_UNESCAPED_UNICODE));
        break;
    }
}
?>
