// js/firebase-config.js
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-auth.js";

// Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyAymaa8NhEe-NvIYwNxiKAU_mMlzOXvvoQ",
  authDomain: "guardianinbox-458f1.firebaseapp.com",
  projectId: "guardianinbox-458f1",
  storageBucket: "guardianinbox-458f1.appspot.com",
  messagingSenderId: "162573718156",
  appId: "1:162573718156:web:dcbef4dd97538e8410a1a9",
  measurementId: "G-99SCJ3V5C0"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Export auth for use in other files
export { auth };