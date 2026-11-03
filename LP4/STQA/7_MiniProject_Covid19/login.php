<?php
require "config.php";

$error = "";
$username = "";

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $username = trim($_POST["username"] ?? "");
    $password = $_POST["password"] ?? "";

    if ($username === "" || $password === "") {
        $error = "Enter username and password";
    } else {
        $stmt = $db->prepare("SELECT id, username, password FROM users WHERE username = ?");
        $stmt->bind_param("s", $username);
        $stmt->execute();
        $user = $stmt->get_result()->fetch_assoc();

        if ($user && password_verify($password, $user["password"])) {
            session_regenerate_id(true);
            $_SESSION["user_id"] = $user["id"];
            $_SESSION["username"] = $user["username"];
            header("Location: index.php");
            exit;
        }
        $error = "Invalid username or password";
    }
}

header_html("Login");
?>
<section class="card form-card">
  <h2>Login</h2>
  <?php if (isset($_SESSION["flash"])): ?>
    <p class="success"><?= h($_SESSION["flash"]) ?></p>
    <?php unset($_SESSION["flash"]); ?>
  <?php endif; ?>
  <?php if ($error): ?><p class="error" id="login-error"><?= h($error) ?></p><?php endif; ?>
  <form method="post">
    <label for="username">Username</label>
    <input type="text" id="username" name="username" value="<?= h($username) ?>">
    <label for="password">Password</label>
    <input type="password" id="password" name="password">
    <button type="submit">Login</button>
  </form>
  <p>New user? <a href="register.php">Register here</a></p>
</section>
<?php footer_html(); ?>
