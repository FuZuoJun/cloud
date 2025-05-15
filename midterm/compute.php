<?php
$node = gethostname();
$jobDir = "/share/jobs/";
$resultDir = "/share/results/";
$jobs = glob($jobDir . "*.json");

foreach ($jobs as $metaFile) {
    $meta = json_decode(file_get_contents($metaFile), true);
    if ($meta['status'] === 'queued' && $meta['assigned_node'] === $node) {
        $csvPath = $jobDir . $meta['filename'];
        $rows = array_map('str_getcsv', file($csvPath));
        $cols = array();

        foreach ($rows as $row) {
            foreach ($row as $i => $val) {
                $cols[$i][] = floatval($val);
            }
        }

        $result = "";
        foreach ($cols as $i => $col) {
            $sum = array_sum($col);
            $avg = $sum / count($col);
            $result .= "第" . ($i + 1) . "欄平均為: $avg，總和為: $sum\n";
        }
        $result .= "此任務由 $node 執行完成。";

        file_put_contents($resultDir . $meta['jobId'] . ".txt", $result);
        $meta['status'] = 'done';
        file_put_contents($metaFile, json_encode($meta));
        break;
    }
}
?>
