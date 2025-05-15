<?php
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $jobId = "job_" . time();
    $uploadDir = "/share/jobs/";
    $filename = $jobId . ".csv";
    $filepath = $uploadDir . $filename;
    if (move_uploaded_file($_FILES['csvfile']['tmp_name'], $filepath)) {
        $nodes = ["computingNode", "computingNode2", "computingNode3"];
        $assigned_node = $nodes[array_rand($nodes)];

        $meta = [
            "jobId" => $jobId,
            "status" => "queued",
            "assigned_node" => $assigned_node,
            "filename" => $filename
        ];
        file_put_contents($uploadDir . $jobId . ".json", json_encode($meta));
        echo "上傳成功，任務ID：$jobId，已指派給：$assigned_node<br>";
    } else {
        echo "上傳失敗";
    }
}
?>
<form method="post" enctype="multipart/form-data">
    上傳 CSV 檔案：<input type="file" name="csvfile">
    <input type="submit" value="上傳">
</form>
