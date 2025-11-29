tailwind.config = {
  darkMode: "class", // Mengaktifkan toggle manual menggunakan class 'dark'
};

// Set theme immediately to prevent flash
(function () {
  const storedTheme = localStorage.getItem("theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

  if (storedTheme === "light" || (!storedTheme && !prefersDark)) {
    document.documentElement.classList.remove("dark");
  } else {
    document.documentElement.classList.add("dark");
  }
})();

// Import Firebase modules for setup (required for Canvas environment)
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-app.js";
import {
  getAuth,
  signInAnonymously,
  signInWithCustomToken,
  onAuthStateChanged,
} from "https://www.gstatic.com/firebasejs/11.6.1/firebase-auth.js";
import {
  getFirestore,
  setDoc,
  doc,
  collection,
  addDoc,
  getDocs,
  orderBy,
  query,
  Timestamp,
} from "https://www.gstatic.com/firebasejs/11.6.1/firebase-firestore.js";

// --- Global Firebase and API Setup ---
let db, auth;
let currentUserId = "anonymous";
const chatHistory = [];
let isFetching = false;
let currentChatId = null;

// Access environment variables (MANDATORY)
const appId = typeof __app_id !== "undefined" ? __app_id : "default-app-id";
const firebaseConfig =
  typeof __firebase_config !== "undefined"
    ? JSON.parse(__firebase_config)
    : null;
const initialAuthToken =
  typeof __initial_auth_token !== "undefined" ? __initial_auth_token : null;
const apiKey = ""; // API Key for Gemini is handled by the environment if left blank
const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${apiKey}`;

// --- UI Elements ---
const sidebar = document.getElementById("sidebar");
const overlay = document.getElementById("sidebar-overlay");
const openBtn = document.getElementById("open-sidebar-btn");
const appIconHeader = document.getElementById("app-icon-header");
const newChatHeaderBtn = document.getElementById("new-chat-header-btn");
const newChatSidebarBtn = document.getElementById("new-chat-sidebar-btn");
const toggleBtn = document.getElementById("sidebar-toggle-btn");
const toggleIcon = document.getElementById("sidebar-toggle-icon");
const chatInput = document.getElementById("chat-input");
const mainContent = document.getElementById("main-content");
const themeToggleBtn = document.getElementById("theme-toggle-btn");
const themeIcon = document.getElementById("theme-icon");
const html = document.documentElement;
const chatHistoryContainer = document.getElementById("chat-history");
const chatHistoryList = document.getElementById("chat-history-list");
const conversationContainer = document.getElementById("conversation-container");
const sendButton = document.getElementById("send-button");
const userStatusText = document.getElementById("user-status-text");
const chatTitle = document.getElementById("chat-title");

// Initialize Lucide Icons
lucide.createIcons();

// --- Firebase Initialization and Authentication ---
async function initializeFirebase() {
  if (!firebaseConfig) {
    console.error("Firebase configuration is missing.");
    userStatusText.textContent = "Mode Demo";
    return;
  }

  try {
    const app = initializeApp(firebaseConfig);
    db = getFirestore(app);
    auth = getAuth(app);

    onAuthStateChanged(auth, async (user) => {
      if (user) {
        currentUserId = user.uid;
        userStatusText.textContent = `User ID: ${user.uid.substring(0, 8)}...`;
        // Set a placeholder user document (MANDATORY for security rules)
        await setDoc(
          doc(db, "artifacts", appId, "users", currentUserId),
          { lastActive: new Date() },
          { merge: true }
        ).catch(console.error);
        console.log("Firebase Auth Ready. User ID:", currentUserId);

        // Load chat history after authentication
        loadChatHistory();
      } else {
        userStatusText.textContent = "Anonim";
        // Fallback to anonymous sign-in if no custom token is available
        if (!initialAuthToken) {
          await signInAnonymously(auth).catch(console.error);
        }
      }
    });

    if (initialAuthToken) {
      try {
        await signInWithCustomToken(auth, initialAuthToken);
      } catch (error) {
        console.error("Error signing in with custom token:", error);
        await signInAnonymously(auth).catch(console.error);
      }
    } else {
      // Initiate anonymous sign-in if no custom token is provided
      await signInAnonymously(auth).catch(console.error);
    }
  } catch (error) {
    console.error("Firebase initialization failed:", error);
    userStatusText.textContent = "Mode Demo";
  }
}

// --- Chat History Management ---
async function loadChatHistory() {
  try {
    const chatsQuery = query(
      collection(db, "artifacts", appId, "users", currentUserId, "chats"),
      orderBy("lastUpdated", "desc")
    );
    const querySnapshot = await getDocs(chatsQuery);

    chatHistoryList.innerHTML = "";

    if (querySnapshot.empty) {
      chatHistoryList.innerHTML = `
              <p class="p-2 text-xs text-gray-400 dark:text-gray-500 px-2">
                Belum ada riwayat obrolan.
              </p>
            `;
      return;
    }

    querySnapshot.forEach((doc) => {
      const chat = doc.data();
      const chatElement = document.createElement("div");
      chatElement.className =
        "flex items-center space-x-3 p-3 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition cursor-pointer";
      chatElement.innerHTML = `
              <i data-lucide="message-circle" class="w-4 h-4 flex-shrink-0 text-gray-400"></i>
              <span class="whitespace-nowrap overflow-hidden text-ellipsis flex-1">${chat.title}</span>
            `;
      chatElement.addEventListener("click", () => loadChat(doc.id, chat));
      chatHistoryList.appendChild(chatElement);
    });

    lucide.createIcons();
  } catch (error) {
    console.error("Error loading chat history:", error);
    chatHistoryList.innerHTML = `
            <p class="p-2 text-xs text-red-400 dark:text-red-500 px-2">
              Gagal memuat riwayat.
            </p>
          `;
  }
}

async function saveChatMessage(role, text) {
  if (!currentChatId) {
    // Create new chat
    const chatData = {
      title: text.length > 30 ? text.substring(0, 30) + "..." : text,
      lastUpdated: Timestamp.now(),
      createdAt: Timestamp.now(),
    };

    try {
      const docRef = await addDoc(
        collection(db, "artifacts", appId, "users", currentUserId, "chats"),
        chatData
      );
      currentChatId = docRef.id;
      chatTitle.textContent = chatData.title;
    } catch (error) {
      console.error("Error creating chat:", error);
    }
  }

  // Save message
  if (currentChatId) {
    try {
      await addDoc(
        collection(
          db,
          "artifacts",
          appId,
          "users",
          currentUserId,
          "chats",
          currentChatId,
          "messages"
        ),
        {
          role,
          text,
          timestamp: Timestamp.now(),
        }
      );

      // Update chat lastUpdated
      await setDoc(
        doc(
          db,
          "artifacts",
          appId,
          "users",
          currentUserId,
          "chats",
          currentChatId
        ),
        { lastUpdated: Timestamp.now() },
        { merge: true }
      );
    } catch (error) {
      console.error("Error saving message:", error);
    }
  }
}

async function loadChat(chatId, chatData) {
  try {
    const messagesQuery = query(
      collection(
        db,
        "artifacts",
        appId,
        "users",
        currentUserId,
        "chats",
        chatId,
        "messages"
      ),
      orderBy("timestamp", "asc")
    );
    const querySnapshot = await getDocs(messagesQuery);

    // Clear current chat
    chatHistory.length = 0;
    chatHistoryContainer.innerHTML = "";
    currentChatId = chatId;
    chatTitle.textContent = chatData.title;

    querySnapshot.forEach((doc) => {
      const message = doc.data();
      appendMessage(message.role, message.text);
      chatHistory.push({
        role: message.role,
        parts: [{ text: message.text }],
      });
    });

    // Close sidebar on mobile
    if (window.innerWidth < 768) {
      toggleSidebar(false, true);
    }
  } catch (error) {
    console.error("Error loading chat:", error);
  }
}

// --- Chat Message Rendering with Code Highlighting ---

/**
 * Creates the HTML structure for a single chat message.
 * @param {string} role 'user' or 'model'
 * @param {string} text Message content
 * @returns {string} HTML string
 */
function createMessageHtml(role, text) {
  const isUser = role === "user";

  let iconHtml;
  let bubbleClasses;
  let alignmentClasses;
  let name;

  if (isUser) {
    iconHtml = `<i data-lucide="user" class="w-4 h-4 text-green-600 dark:text-green-400"></i>`;
    bubbleClasses = "bg-blue-600 dark:bg-blue-700 text-white shadow-lg";
    alignmentClasses = "justify-end";
    name = "Anda";
  } else {
    iconHtml = `<i data-lucide="sparkles" class="w-4 h-4 text-blue-600 dark:text-blue-400"></i>`;
    bubbleClasses =
      "bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 shadow-lg border border-gray-100 dark:border-gray-700";
    alignmentClasses = "justify-start";
    name = "AI Assistant";
  }

  const avatarContainerClasses = isUser
    ? "bg-green-100 dark:bg-green-900/30"
    : "bg-blue-100 dark:bg-blue-900/30";

  const contentDirectionClasses = isUser
    ? "flex-row-reverse space-x-3 space-x-reverse"
    : "space-x-3";

  // Convert Markdown text to basic HTML with code highlighting
  const formattedText = formatMessageText(text);

  return `
          <div class="flex ${alignmentClasses}">
            <div class="flex items-start ${contentDirectionClasses} max-w-full">
              <div class="w-8 h-8 flex-shrink-0 ${avatarContainerClasses} rounded-full flex items-center justify-center">
                ${iconHtml}
              </div>
              <div class="p-4 rounded-xl transition-colors ${bubbleClasses} message-bubble max-w-3xl overflow-hidden break-words">
                <p class="font-medium ${
                  isUser ? "mb-1" : "text-gray-800 dark:text-white mb-1"
                }">${name}</p>
                <div class="text-sm leading-relaxed message-content">${formattedText}</div>
              </div>
            </div>
          </div>
        `;
}

/**
 * Format message text with Markdown and code highlighting
 * @param {string} text Message text
 * @returns {string} Formatted HTML
 */
function formatMessageText(text) {
  // Process code blocks first
  let formattedText = text.replace(
    /```(\w+)?\n([\s\S]*?)```/g,
    (match, language, code) => {
      const lang = language || "text";
      const escapedCode = code
        .trim()
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
      return `
            <div class="code-block my-3 rounded-lg overflow-hidden">
              <div class="flex items-center justify-between bg-gray-800 px-4 py-2">
                <span class="text-xs text-gray-300 font-mono">${lang}</span>
                <button class="copy-btn bg-gray-700 hover:bg-gray-600 text-gray-300 text-xs px-2 py-1 rounded flex items-center space-x-1 transition" onclick="copyCode(this)">
                  <i data-lucide="copy" class="w-3 h-3"></i>
                  <span>Salin</span>
                </button>
              </div>
              <pre class="bg-gray-900 p-4 overflow-x-auto"><code class="language-${lang}">${escapedCode}</code></pre>
            </div>
          `;
    }
  );

  // Process inline code
  formattedText = formattedText.replace(
    /`([^`]+)`/g,
    '<code class="bg-gray-100 dark:bg-gray-700 px-1 py-0.5 rounded text-sm font-mono">$1</code>'
  );

  // Process other Markdown
  formattedText = formattedText
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>") // Bold
    .replace(/\*(.*?)\*/g, "<em>$1</em>") // Italic
    .replace(/\n\s*\n/g, '</p><p class="leading-relaxed mt-2">') // New paragraphs
    .replace(/\n/g, "<br>"); // Line breaks

  return `<p class="leading-relaxed">${formattedText}</p>`;
}

/**
 * Appends a new message to the chat history and scrolls to the bottom.
 * @param {string} role 'user' or 'model'
 * @param {string} text Message content
 * @param {string} [id] ID for the message div (useful for loading state)
 */
function appendMessage(role, text, id = null) {
  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = createMessageHtml(role, text);
  const messageElement = tempDiv.firstChild;

  if (id) {
    messageElement.id = id;
  }

  chatHistoryContainer.appendChild(messageElement);

  // Apply syntax highlighting to code blocks
  messageElement.querySelectorAll("pre code").forEach((block) => {
    hljs.highlightElement(block);
  });

  lucide.createIcons(); // Re-render icons in new content

  // Scroll to the bottom
  conversationContainer.scrollTop = conversationContainer.scrollHeight;

  return messageElement;
}

/**
 * Updates an existing AI message, typically used to replace the loading indicator.
 * @param {string} id The ID of the message element to update
 * @param {string} text The new message content
 */
function updateMessage(id, text) {
  const oldElement = document.getElementById(id);
  if (oldElement) {
    const newHtml = createMessageHtml("model", text);
    oldElement.outerHTML = newHtml;

    // Apply syntax highlighting to code blocks
    oldElement.parentElement.querySelectorAll("pre code").forEach((block) => {
      hljs.highlightElement(block);
    });

    lucide.createIcons();
    conversationContainer.scrollTop = conversationContainer.scrollHeight;
  }
}

// --- Copy Code Function ---
window.copyCode = function (button) {
  const codeBlock = button.closest(".code-block");
  const code = codeBlock.querySelector("code").textContent;

  navigator.clipboard
    .writeText(code)
    .then(() => {
      const originalText = button.innerHTML;
      button.innerHTML =
        '<i data-lucide="check" class="w-3 h-3"></i><span>Disalin!</span>';
      lucide.createIcons();

      setTimeout(() => {
        button.innerHTML = originalText;
        lucide.createIcons();
      }, 2000);
    })
    .catch((err) => {
      console.error("Failed to copy code: ", err);
    });
};

// --- Gemini API Logic (with Exponential Backoff) ---

/**
 * Sends the chat history to the Gemini API and handles retries.
 * @param {number} retryCount Current retry attempt
 */
async function makeApiCall(retryCount = 0) {
  const maxRetries = 5;
  const userQuery = chatHistory[chatHistory.length - 1].parts[0].text;
  const systemPrompt =
    "Anda adalah AI Assistant yang canggih. Jawab pertanyaan pengguna dengan gaya yang membantu dan profesional. Jika diminta membuat kode atau dokumen, sediakan dalam format Markdown di dalam file block.";

  const payload = {
    contents: chatHistory,
    tools: [{ google_search: {} }], // Enable search grounding
    systemInstruction: { parts: [{ text: systemPrompt }] },
  };

  try {
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      // If rate limit or other temporary errors occur, retry
      if (response.status === 429 || response.status >= 500) {
        throw new Error(`Temporary API error (${response.status})`);
      }
      // For other errors, do not retry
      const errorData = await response.json();
      throw new Error(
        `API Error: ${errorData.error.message || response.statusText}`
      );
    }

    const result = await response.json();
    const candidate = result.candidates?.[0];

    if (candidate && candidate.content?.parts?.[0]?.text) {
      const text = candidate.content.parts[0].text;

      // Add the AI response to chat history
      chatHistory.push({ role: "model", parts: [{ text: text }] });
      return text;
    } else {
      throw new Error("Invalid response format from API.");
    }
  } catch (error) {
    if (retryCount < maxRetries) {
      const delay = Math.pow(2, retryCount) * 1000 + Math.random() * 1000;
      await new Promise((resolve) => setTimeout(resolve, delay));
      return makeApiCall(retryCount + 1);
    } else {
      console.error("API call failed after maximum retries:", error);
      return `Maaf, terjadi kesalahan saat menghubungi layanan AI: ${error.message}`;
    }
  }
}

/**
 * Handles the full sending process: UI update, API call, and result display.
 */
async function sendMessage() {
  if (isFetching || chatInput.value.trim() === "") return;

  const userText = chatInput.value.trim();
  const tempAiId = "ai-loading-" + Date.now();

  // 1. Reset UI and set fetching state
  chatInput.value = "";
  adjustTextareaHeight();
  isFetching = true;
  sendButton.disabled = true;

  // 2. Append User Message and Add to History
  appendMessage("user", userText);
  chatHistory.push({ role: "user", parts: [{ text: userText }] });

  // 3. Save user message to database
  await saveChatMessage("user", userText);

  // 4. Update chat title with first message
  if (chatHistory.length === 1) {
    const shortText =
      userText.length > 30 ? userText.substring(0, 30) + "..." : userText;
    chatTitle.textContent = shortText;
  }

  // 5. Append Loading Message
  const loadingMessage = `
            <div class="flex items-center space-x-2">
                <i data-lucide="loader-circle" class="w-4 h-4 animate-spin-slow text-blue-500"></i>
                <span class="text-sm text-gray-500 dark:text-gray-400">AI sedang mengetik...</span>
            </div>
        `;
  appendMessage("model", loadingMessage, tempAiId);

  // 6. Call API
  try {
    const aiResponseText = await makeApiCall();
    updateMessage(tempAiId, aiResponseText);

    // Save AI response to database
    await saveChatMessage("model", aiResponseText);

    // Reload chat history to show updated list
    loadChatHistory();
  } catch (error) {
    console.error("Fatal error during chat process:", error);
    updateMessage(
      tempAiId,
      `❌ **Kesalahan Fatal:** Tidak dapat memproses permintaan. Silakan coba lagi.`
    );
  } finally {
    // 7. Reset fetching state
    isFetching = false;
    if (chatInput.value.trim() !== "") {
      sendButton.disabled = false;
    }
  }
}

// --- New Chat Functionality ---
function startNewChat() {
  // Clear chat history
  chatHistory.length = 0;
  chatHistoryContainer.innerHTML = "";
  currentChatId = null;

  // Reset chat title
  chatTitle.textContent = "Obrolan AI Baru";

  // Add welcome message back
  const welcomeMessage = `
          <div class="flex justify-center text-center pt-8">
            <div class="max-w-lg p-6 rounded-xl bg-white dark:bg-gray-800 shadow-xl border border-gray-100 dark:border-gray-700/50">
              <i data-lucide="sparkles" class="w-8 h-8 mx-auto mb-3 text-blue-600 dark:text-blue-400"></i>
              <h2 class="text-xl font-bold mb-2">Halo! Saya Gemini.</h2>
              <p class="text-gray-600 dark:text-gray-300">
                Tanyakan apapun yang Anda butuhkan: ide coding, analisis,
                penulisan esai, atau buatkan aplikasi web di editor di sebelah
                kanan.
              </p>
            </div>
          </div>
        `;
  chatHistoryContainer.innerHTML = welcomeMessage;
  lucide.createIcons();

  // Clear input
  chatInput.value = "";
  adjustTextareaHeight();
  sendButton.disabled = true;

  // Close sidebar on mobile after starting new chat
  if (window.innerWidth < 768) {
    toggleSidebar(false, true);
  }
}

// --- UI Interaction Handlers ---

// Toggle Sidebar
function toggleSidebar(forceOpen = false, forceClose = false) {
  const isHidden = sidebar.classList.contains("-translate-x-full");
  const isDesktop = window.innerWidth >= 768;

  let shouldOpen = forceOpen || (isHidden && !forceClose);
  let shouldClose = forceClose || (!isHidden && !forceOpen);

  if (shouldClose) {
    sidebar.classList.add("-translate-x-full");
    if (!isDesktop) {
      overlay.classList.add("opacity-0", "pointer-events-none");
      overlay.classList.remove("opacity-50");
    }
    openBtn.style.display = "block";
    newChatHeaderBtn.style.display = "block";
    // Tampilkan icon app saat sidebar tertutup (hanya di desktop)
    if (isDesktop) {
      appIconHeader.style.display = "flex";
    }
    toggleIcon.setAttribute("data-lucide", "chevrons-right");
    if (isDesktop) mainContent.classList.remove("md:ml-64");
  } else if (shouldOpen) {
    sidebar.classList.remove("-translate-x-full");
    if (!isDesktop) {
      overlay.classList.remove("opacity-0", "pointer-events-none");
      overlay.classList.add("opacity-50");
    }
    openBtn.style.display = "none";
    newChatHeaderBtn.style.display = "none";
    // Sembunyikan icon app saat sidebar terbuka
    appIconHeader.style.display = "none";
    toggleIcon.setAttribute("data-lucide", "chevrons-left");
    if (isDesktop) mainContent.classList.add("md:ml-64");
  }
  lucide.createIcons();
}

toggleBtn.addEventListener("click", () => toggleSidebar(false, true));
openBtn.addEventListener("click", () => toggleSidebar(true, false));
overlay.addEventListener("click", () => toggleSidebar(false, true));

// New Chat buttons
newChatSidebarBtn.addEventListener("click", (e) => {
  e.preventDefault();
  startNewChat();
});

newChatHeaderBtn.addEventListener("click", (e) => {
  e.preventDefault();
  startNewChat();
});

// Theme Toggle - Perbaikan untuk menghindari flash
function initializeTheme() {
  // Theme sudah diatur di script awal, cukup update icon saja
  const isDark = html.classList.contains("dark");
  themeIcon.setAttribute("data-lucide", isDark ? "sun" : "moon");
  lucide.createIcons();
}

themeToggleBtn.addEventListener("click", () => {
  html.classList.toggle("dark");
  const isDark = html.classList.contains("dark");
  localStorage.setItem("theme", isDark ? "dark" : "light");
  themeIcon.setAttribute("data-lucide", isDark ? "sun" : "moon");
  lucide.createIcons();
});

// Textarea Auto-Resize and Send Button Toggle
function adjustTextareaHeight() {
  chatInput.style.height = "auto";
  const newHeight = Math.min(chatInput.scrollHeight, 150);
  chatInput.style.height = newHeight + "px";
}

chatInput.addEventListener("input", () => {
  adjustTextareaHeight();
  // Enable/Disable send button based on input content
  sendButton.disabled = isFetching || chatInput.value.trim() === "";
});

// Send message on click
sendButton.addEventListener("click", sendMessage);

// Send message on Enter, but allow Shift+Enter for new line
chatInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
});

// --- Initialization ---

function setInitialSidebarState() {
  const isDesktop = window.innerWidth >= 768;
  if (isDesktop) {
    sidebar.classList.remove("-translate-x-full");
    toggleIcon.setAttribute("data-lucide", "chevrons-left");
    openBtn.style.display = "none";
    newChatHeaderBtn.style.display = "none";
    // Icon app disembunyikan saat sidebar terbuka di awal
    appIconHeader.style.display = "none";
    mainContent.classList.add("md:ml-64");
  } else {
    sidebar.classList.add("-translate-x-full");
    toggleIcon.setAttribute("data-lucide", "chevrons-right");
    openBtn.style.display = "block";
    newChatHeaderBtn.style.display = "block";
    // Icon app tetap tersembunyi di mobile
    appIconHeader.style.display = "none";
    mainContent.classList.remove("md:ml-64");
  }
  lucide.createIcons();
}

window.addEventListener("resize", setInitialSidebarState);

window.onload = function () {
  initializeFirebase();
  initializeTheme(); // Hanya update icon, tema sudah diatur di awal
  setInitialSidebarState();
  // Ensure initial height is correct
  adjustTextareaHeight();

  // Focus on chat input for better UX
  setTimeout(() => {
    chatInput.focus();
  }, 500);
};
