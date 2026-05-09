function togglePassword(inputId) {
  const input = document.getElementById(inputId);
  if (!input) return;
  input.type = input.type === 'password' ? 'text' : 'password';
}

function selectRole(buttonEl) {
  document.querySelectorAll('.role-btn').forEach((b) => b.classList.remove('active'));
  buttonEl.classList.add('active');
}

function getSelectedRole() {
  const activeRole = document.querySelector('.role-btn.active');
  return activeRole ? activeRole.dataset.role : 'user';
}

document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = loginForm.querySelector('input[type="email"]').value.trim();
      const passwordInput = document.getElementById('password');
      const password = passwordInput ? passwordInput.value : '';
      const role = getSelectedRole();
      try {
        const res = await fetch('/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, role }),
        });
        const text = await res.text();
        const j = text ? JSON.parse(text) : {};
        if (j.ok) {
          window.location.href = j.redirect || (j.role === 'admin' ? '/admin/dashboard' : '/dashboard');
        } else {
          alert(j.error || `Login failed (${res.status})`);
        }
      } catch (err) {
        console.error(err);
        alert(err.message || 'Network error');
      }
    });
  }

  const signupForm = document.getElementById('signupForm');
  if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = signupForm.querySelector('input[type="text"]').value.trim();
      const email = signupForm.querySelector('input[type="email"]').value.trim();
      const passwordInput = document.getElementById('signup_password');
      const password = passwordInput ? passwordInput.value : '';
      // detect selected role (if any)
      const role = getSelectedRole();
      let admin_secret = undefined;
      if (role === 'admin') {
        admin_secret = prompt('Admin secret (required to create admin)');
      }
      try {
        const res = await fetch('/api/signup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ full_name: name, email, password, role, admin_secret }),
        });
        const text = await res.text();
        const j = text ? JSON.parse(text) : {};
        if (j.ok) {
          window.location.href = j.redirect || '/login';
        } else {
          alert(j.error || `Signup failed (${res.status})`);
        }
      } catch (err) {
        console.error(err);
        alert(err.message || 'Network error');
      }
    });
  }
});
