<?php
require "config.php";
header_html("Home");

$stats = $db->query("SELECT * FROM covid_stats ORDER BY confirmed DESC");
$comments = $db->query(
    "SELECT c.comment, c.created_at, u.username
     FROM comments c JOIN users u ON u.id = c.user_id
     ORDER BY c.created_at DESC LIMIT 20"
);
?>

<section class="hero">
  <h1>COVID-19 Information Portal</h1>
  <p>Symptoms, prevention, vaccination and state-wise statistics.</p>
</section>

<div class="grid">
  <section class="card">
    <h2>Symptoms</h2>
    <ul>
      <li>Fever or chills</li>
      <li>Dry cough, sore throat</li>
      <li>Tiredness, body ache</li>
      <li>Loss of taste or smell</li>
      <li>Difficulty breathing (seek care immediately)</li>
    </ul>
  </section>

  <section class="card">
    <h2>Prevention</h2>
    <ul>
      <li>Wear a mask in crowded places</li>
      <li>Wash hands for 20 seconds</li>
      <li>Keep 6 feet distance</li>
      <li>Get fully vaccinated, including booster</li>
      <li>Isolate if you test positive</li>
    </ul>
  </section>

  <section class="card">
    <h2>Vaccination</h2>
    <p>Book a slot on the CoWIN portal or visit the nearest government centre with a photo ID.</p>
    <p>Vaccines: Covishield, Covaxin, Corbevax.</p>
  </section>
</div>

<section class="card">
  <h2>State-wise Statistics <small>(sample figures)</small></h2>
  <table id="stats">
    <tr><th>State</th><th>Confirmed</th><th>Recovered</th><th>Deaths</th><th>Vaccine doses</th></tr>
    <?php while ($s = $stats->fetch_assoc()): ?>
      <tr>
        <td><?= h($s["state"]) ?></td>
        <td><?= number_format($s["confirmed"]) ?></td>
        <td><?= number_format($s["recovered"]) ?></td>
        <td><?= number_format($s["deaths"]) ?></td>
        <td><?= number_format($s["vaccinated"]) ?></td>
      </tr>
    <?php endwhile; ?>
  </table>
</section>

<section class="card">
  <h2>Comments</h2>

  <?php if (isset($_SESSION["user_id"])): ?>
    <form method="post" action="comment.php" class="validate">
      <textarea name="comment" id="comment" data-rule="comment" rows="3"
                placeholder="Share information or ask a question"></textarea>
      <span class="error" data-for="comment"><?= h($_SESSION["comment_error"] ?? "") ?></span>
      <button type="submit">Post Comment</button>
    </form>
    <?php unset($_SESSION["comment_error"]); ?>
  <?php else: ?>
    <p><a href="login.php">Login</a> to post a comment.</p>
  <?php endif; ?>

  <ul class="comments">
    <?php while ($c = $comments->fetch_assoc()): ?>
      <li>
        <b><?= h($c["username"]) ?></b> <small><?= h($c["created_at"]) ?></small>
        <p><?= nl2br(h($c["comment"])) ?></p>
      </li>
    <?php endwhile; ?>
  </ul>
</section>

<?php footer_html(); ?>
