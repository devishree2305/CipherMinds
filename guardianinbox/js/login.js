import { auth } from "./firebase-config.js";
import { signInWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-auth.js";

// Login function
function login() {
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;

  signInWithEmailAndPassword(auth, email, password)
    .then((userCredential) => {
      // Signed in
      const user = userCredential.user;
      alert("Login successful!");
      window.location.href = "dashboard.html"; // Redirect to dashboard or another page
    })
    .catch((error) => {
      const errorCode = error.code;
      const errorMessage = error.message;
      alert("Login failed: " + errorMessage);
    });
}

// Attach login function to the button
document.querySelector('button').addEventListener('click', login);