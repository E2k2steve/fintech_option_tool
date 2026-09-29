"use strict";
const form = document.getElementById("pricing-form");
const button = document.getElementById("calculate-button");
const notice = document.getElementById("dirty-notice");
form.addEventListener("input", () => { notice.hidden = false; });
form.addEventListener("submit", () => {
  if (form.checkValidity()) {
    button.disabled = true;
    button.textContent = "正在计算…";
    form.setAttribute("aria-busy", "true");
  }
});
window.addEventListener("pageshow", () => {
  button.disabled = false;
  button.textContent = "计算价格与风险 ↗";
  form.removeAttribute("aria-busy");
});
