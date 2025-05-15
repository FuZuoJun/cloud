<?php
$uploadDir = "/share/jobs/";
if (!is_dir($uploadDir)) {
    mkdir($uploadDir, 0777, true);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $file = $_FILES['textfile'];
    $keywords = array_filter(array_map('trim', $_POST['keywords'] ?? []));

    if ($file['error'] !== UPLOAD_ERR_OK || empty($keywords)) {
        echo "❌ 請選擇檔案並至少輸入一個關鍵字。";
        exit;
    }

    $jobId = "job_" . time();
    $filename = $jobId . ".txt";
    $filepath = $uploadDir . $filename;
    move_uploaded_file($file['tmp_name'], $filepath);

    $nodes = ["computingNode1", "computingNode2", "computingNode3"];
    $assigned_node = $nodes[array_rand($nodes)];

    $meta = [
        "jobId" => $jobId,
        "status" => "queued",
        "assigned_node" => $assigned_node,
        "filename" => $filename,
        "keywords" => $keywords
    ];
    file_put_contents($uploadDir . $jobId . ".json", json_encode($meta, JSON_UNESCAPED_UNICODE));
    echo "✅ 上傳成功！任務 ID：$jobId<br>📦 已指派給節點：$assigned_node<br>";
}
?>

<form method="post" enctype="multipart/form-data">
    <label>上傳文字檔：<input type="file" name="textfile" required></label><br>
    <label>關鍵字1：<input type="text" name="keywords[]"></label><br>
    <label>關鍵字2：<input type="text" name="keywords[]"></label><br>
    <label>關鍵字3：<input type="text" name="keywords[]"></label><br>
    <input type="submit" value="提交任務">
</form>
