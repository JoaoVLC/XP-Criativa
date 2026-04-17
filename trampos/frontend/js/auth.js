/* ─────────────────────────────────────────────────────────────
   auth.js  –  shared utilities for all Trampos pages
   ───────────────────────────────────────────────────────────── */

const API = "http://localhost:8000";

/* ── Session ──────────────────────────────────────────────── */

function getUser() {
  try { return JSON.parse(localStorage.getItem("trampos_user")); }
  catch { return null; }
}

function setUser(user) {
  localStorage.setItem("trampos_user", JSON.stringify(user));
}

function logout() {
  localStorage.removeItem("trampos_user");
  window.location.href = "login.html";
}

/* ── Route guards ─────────────────────────────────────────── */

function requireLogin() {
  const user = getUser();
  if (!user) { window.location.href = "login.html"; return null; }
  return user;
}

function requireTipo(tipo) {
  const user = requireLogin();
  if (user && user.tipo !== tipo) { window.location.href = "index.html"; return null; }
  return user;
}

/* ── Nav ──────────────────────────────────────────────────── */

function renderNav(active = "") {
  const nav = document.getElementById("main-nav");
  if (!nav) return;
  const user = getUser();
  nav.innerHTML = `
    <div class="nav-brand">
      <a href="${user ? 'index.html' : 'login.html'}">🔧 Trampos</a>
    </div>
    <button class="nav-toggle" onclick="toggleNav()" aria-label="Abrir menu">&#9776;</button>
    <div class="nav-menu" id="nav-menu">
      <a href="index.html" class="${active === 'vagas' ? 'active' : ''}">Vagas</a>
      ${user && user.tipo === 'empresa'
        ? `<a href="create-job.html" class="${active === 'criar' ? 'active' : ''}">Publicar Vaga</a>`
        : ''}
      ${user
        ? `<a href="profile.html" class="nav-user ${active === 'perfil' ? 'active' : ''}">
             <span class="nav-avatar">${user.nome[0].toUpperCase()}</span>
             ${user.nome.split(' ')[0]}
           </a>
           <button class="btn-nav-ghost" onclick="logout()">Sair</button>`
        : `<a href="login.html" class="btn-nav-primary ${active === 'login' ? 'active' : ''}">Entrar</a>`
      }
    </div>
  `;
}

function toggleNav() {
  document.getElementById("nav-menu")?.classList.toggle("open");
}

/* ── Toast notifications ──────────────────────────────────── */

function showToast(msg, type = "success") {
  let box = document.getElementById("toast-box");
  if (!box) {
    box = document.createElement("div");
    box.id = "toast-box";
    document.body.appendChild(box);
  }
  const t = document.createElement("div");
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  box.appendChild(t);
  requestAnimationFrame(() => t.classList.add("show"));
  setTimeout(() => { t.classList.remove("show"); setTimeout(() => t.remove(), 300); }, 3500);
}

/* ── Confirm modal ────────────────────────────────────────── */

function showModal(title, message, onConfirm) {
  let overlay = document.getElementById("confirm-modal");
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.id = "confirm-modal";
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="modal-box">
        <h3 id="modal-title"></h3>
        <p id="modal-msg"></p>
        <div class="modal-btns">
          <button class="btn btn-ghost" onclick="closeModal()">Cancelar</button>
          <button class="btn btn-danger" id="modal-ok">Confirmar</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);
  }
  document.getElementById("modal-title").textContent = title;
  document.getElementById("modal-msg").textContent = message;
  document.getElementById("modal-ok").onclick = () => { closeModal(); onConfirm(); };
  overlay.classList.add("open");
}

function closeModal() {
  document.getElementById("confirm-modal")?.classList.remove("open");
}

/* ── Form validation ──────────────────────────────────────── */

const regex = {
  email:     /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/,
  nome:      /^[a-zA-ZÀ-ÿ\s]{3,100}$/,
  senha:     /^.{6,}$/,
  titulo:    /^.{5,}$/,
  local:     /^.{3,}$/,
  descricao: /^[\s\S]{20,}$/,
};

function validate(input, rule, msg) {
  const ok = rule.test(input.value.trim());
  setFieldState(input, ok, ok ? "" : msg);
  return ok;
}

function setFieldState(input, valid, msg = "") {
  input.classList.toggle("input-error", !valid);
  input.classList.toggle("input-ok",    valid && input.value.trim() !== "");
  const err = input.closest(".form-group")?.querySelector(".field-error");
  if (err) err.textContent = msg;
}

function clearValidation(form) {
  form.querySelectorAll(".input-error, .input-ok").forEach(el => {
    el.classList.remove("input-error", "input-ok");
  });
  form.querySelectorAll(".field-error").forEach(el => el.textContent = "");
}

/* ── Helpers ──────────────────────────────────────────────── */

function formatDate(str) {
  if (!str) return "";
  const [y, m, d] = str.split("-");
  return `${d}/${m}/${y}`;
}

function formatMoney(val) {
  return Number(val).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function toggleSenha(id) {
  const el = document.getElementById(id);
  if (el) el.type = el.type === "password" ? "text" : "password";
}
