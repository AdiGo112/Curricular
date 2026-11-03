<?php
require "config.php";

if (!isset($_SESSION["user_id"]) || $_SERVER["REQUEST_METHOD"] !== "POST") {
    header("Location: login.php");
    exit;
}

$comment = trim($_POST["comment"] ?? "");
$error = validate("comment", $comment);

if ($error) {
    $_SESSION["comment_error"] = $error;
} else {
    $stmt = $db->prepare("INSERT INTO comments (user_id, comment) VALUES (?, ?)");
    $stmt->bind_param("is", $_SESSION["user_id"], $comment);
    $stmt->execute();
}

header("Location: index.php");
exit;
