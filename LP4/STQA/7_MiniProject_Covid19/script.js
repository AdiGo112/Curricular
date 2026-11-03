// =========================================================
// Client-side validation using the SAME regex_rules.json as
// the PHP server. The server always validates again, so this
// is only for instant feedback while typing.
// =========================================================

fetch("regex_rules.json")
  .then((r) => r.json())
  .then((rules) => {
    document.querySelectorAll("form.validate").forEach((form) => {
      const inputs = form.querySelectorAll("[data-rule], [data-match]");

      const check = (input) => {
        let msg = "";
        if (input.dataset.rule) {
          const rule = rules[input.dataset.rule];
          const value = input.type === "password" ? input.value : input.value.trim();
          if (!new RegExp("^(?:" + rule.pattern + ")$").test(value)) msg = rule.message;
        } else if (input.value !== form.querySelector("#" + input.dataset.match).value) {
          msg = "Passwords do not match";
        }
        const span = form.querySelector(`.error[data-for="${input.name}"]`);
        if (span) span.textContent = msg;
        input.classList.toggle("invalid", msg !== "");
        return msg === "";
      };

      inputs.forEach((input) => input.addEventListener("input", () => check(input)));

      form.addEventListener("submit", (e) => {
        const allValid = [...inputs].map(check).every(Boolean);
        if (!allValid) e.preventDefault();
      });
    });
  });
