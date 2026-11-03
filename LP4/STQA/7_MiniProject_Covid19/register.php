<?php
require "config.php";

$fields = ["full_name", "username", "email", "phone", "age", "pincode", "password"];
$values = array_fill_keys($fields, "");
$values["vaccinated"] = "None";
$errors = [];

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    foreach ($fields as $f) {
        $values[$f] = trim($_POST[$f] ?? "");
        $msg = validate($f, $values[$f]);
        if ($msg) $errors[$f] = $msg;
    }
    $values["password"] = $_POST["password"] ?? "";   // passwords are not trimmed
    if ($values["password"] !== ($_POST["confirm"] ?? "")) {
        $errors["confirm"] = "Passwords do not match";
    }
    $values["vaccinated"] = $_POST["vaccinated"] ?? "None";
    if (!in_array($values["vaccinated"], ["None", "Dose 1", "Dose 2", "Booster"], true)) {
        $errors["vaccinated"] = "Choose a vaccination status";
    }

    if (!$errors) {
        $check = $db->prepare("SELECT id FROM users WHERE username = ? OR email = ?");
        $check->bind_param("ss", $values["username"], $values["email"]);
        $check->execute();
        if ($check->get_result()->num_rows > 0) {
            $errors["username"] = "Username or email already registered";
        }
    }

    if (!$errors) {
        $hash = password_hash($values["password"], PASSWORD_DEFAULT);
        $age = (int) $values["age"];
        $stmt = $db->prepare(
            "INSERT INTO users (full_name, username, email, phone, age, pincode, vaccinated, password)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        );
        $stmt->bind_param("ssssisss", $values["full_name"], $values["username"], $values["email"],
                          $values["phone"], $age, $values["pincode"], $values["vaccinated"], $hash);
        $stmt->execute();
        $_SESSION["flash"] = "Registration successful. Please login.";
        header("Location: login.php");
        exit;
    }
}

function field($name, $label, $type, $values, $errors) {
    $value = $type === "password" ? "" : h($values[$name] ?? "");
    echo "<label for='$name'>$label</label>";
    echo "<input type='$type' id='$name' name='$name' value='$value' data-rule='$name'>";
    echo "<span class='error' data-for='$name'>" . h($errors[$name] ?? "") . "</span>";
}

header_html("Register");
?>
<section class="card form-card">
  <h2>Register</h2>
  <form method="post" class="validate" novalidate>
    <?php
    field("full_name", "Full name", "text", $values, $errors);
    field("username", "Username", "text", $values, $errors);
    field("email", "Email", "email", $values, $errors);
    field("phone", "Mobile number", "tel", $values, $errors);
    field("age", "Age", "text", $values, $errors);
    field("pincode", "Pincode", "text", $values, $errors);
    ?>
    <label for="vaccinated">Vaccination status</label>
    <select id="vaccinated" name="vaccinated">
      <?php foreach (["None", "Dose 1", "Dose 2", "Booster"] as $v): ?>
        <option <?= $values["vaccinated"] === $v ? "selected" : "" ?>><?= $v ?></option>
      <?php endforeach; ?>
    </select>
    <span class="error"><?= h($errors["vaccinated"] ?? "") ?></span>
    <?php field("password", "Password", "password", $values, $errors); ?>
    <label for="confirm">Confirm password</label>
    <input type="password" id="confirm" name="confirm" data-match="password">
    <span class="error" data-for="confirm"><?= h($errors["confirm"] ?? "") ?></span>
    <button type="submit">Register</button>
  </form>
</section>
<?php footer_html(); ?>
