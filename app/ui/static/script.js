// Import Lucide dan jQuery sudah ditangani di index.html

// Global Setup (Disederhanakan)
let currentUserId = "default"; // Tetapkan ID Sesi Default
let isFetching = false;
const apiUrl = "/api/chat"; // Endpoint FastAPI Anda
const historyApiUrl = "/api/history"; // Endpoint baru untuk memuat riwayat
// Catatan: chatHistory lokal dihapus karena status history sekarang dikelola oleh backend (Orchestrator/Memory)

// jQuery Element Selectors (Tidak Berubah)
const $sidebar = $("#sidebar");
const $overlay = $("#sidebar-overlay");
const $openBtn = $("#open-sidebar-btn");
const $toggleBtn = $("#sidebar-toggle-btn");
const $toggleIcon = $("#sidebar-toggle-icon");
const $chatInput = $("#chat-input");
const $mainContent = $("#main-content");
const $themeToggleBtn = $("#theme-toggle-btn");
const $themeIcon = $("#theme-icon");
const $html = $("html");
const $chatHistoryContainer = $("#chat-history");
const $conversationContainer = $("#conversation-container");
const $sendButton = $("#send-button");
const $userStatusText = $("#user-status-text");
const $chatTitle = $("#chat-title");
const $newChatHeaderBtn = $("#new-chat-header-btn");
const $newChatSidebarBtn = $("#new-chat-sidebar-btn");
const $appIconHeader = $("#app-icon-header");

// **PENTING: Fungsi inisialisasi Firebase/Auth Dihapus!**
// Gantilah status pengguna dengan default.
$userStatusText.text(`User ID: ${currentUserId}`);

// --- Chat Message Rendering (Tidak Berubah) ---

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

  if (isUser) {
    iconHtml = `<i data-lucide="user" class="w-4 h-4 text-green-600 dark:text-green-400"></i>`;
    bubbleClasses = "bg-blue-600 dark:bg-blue-700 text-white shadow-lg";
    alignmentClasses = "justify-end";
  } else {
    iconHtml = `<i data-lucide="sparkles" class="w-4 h-4 text-blue-600 dark:text-blue-400"></i>`;
    bubbleClasses =
      "bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 shadow-lg border border-gray-100 dark:border-gray-700";
    alignmentClasses = "justify-start";
  }

  const avatarContainerClasses = isUser
    ? "bg-green-100 dark:bg-green-900/30"
    : "bg-blue-100 dark:bg-blue-900/30";

  const contentDirectionClasses = isUser
    ? "flex-row-reverse space-x-3 space-x-reverse"
    : "space-x-3";

  // Basic Markdown to HTML conversion
  const formattedText = text
    .trim()
    .replace(/\n\s*\n/g, '</p><p class="leading-relaxed">')
    .replace(/\n/g, "<br>")
    .replace(/```(.*?)\n([\s\S]*?)```/g, (match, p1, p2) => {
      const language = p1.trim() || "text";
      return `<pre class="bg-gray-100 dark:bg-gray-700/50 p-3 rounded-md overflow-x-auto my-2 text-sm"><code class="language-${language}">${p2.trim()}</code></pre>`;
    })
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>");

  return `
    <div class="flex ${alignmentClasses}">
      <div class="flex items-start ${contentDirectionClasses} max-w-full">
        <div class="w-8 h-8 flex-shrink-0 ${avatarContainerClasses} rounded-full flex items-center justify-center">
          ${iconHtml}
        </div>
        <div class="p-4 rounded-xl transition-colors ${bubbleClasses} message-bubble max-w-3xl overflow-hidden break-words">
          <div class="text-sm leading-relaxed">${formattedText}</div>
        </div>
      </div>
    </div>
  `;
}

/**
 * Appends a new message to the chat history and scrolls to the bottom.
 * @param {string} role 'user' or 'model'
 * @param {string} text Message content
 * @param {string} [id] ID for the message div (useful for loading state)
 */
function appendMessage(role, text, id = null) {
  const htmlString = createMessageHtml(role, text);
  const $messageElement = $(htmlString);

  if (id) {
    $messageElement.attr("id", id);
  }

  $chatHistoryContainer.append($messageElement);
  lucide.createIcons();

  // Scroll to the bottom
  $conversationContainer.scrollTop($conversationContainer[0].scrollHeight);

  return $messageElement;
}

/**
 * Updates an existing AI message, typically used to replace the loading indicator.
 * @param {string} id The ID of the message element to update
 * @param {string} text The new message content
 */
function updateMessage(id, text) {
  const $oldElement = $(`#${id}`);
  if ($oldElement.length) {
    const newHtml = createMessageHtml("model", text);
    $oldElement.replaceWith(newHtml);
    lucide.createIcons();
    $conversationContainer.scrollTop($conversationContainer[0].scrollHeight);
  }
}

// --- FastAPI API Logic ---

/**
 * Sends the user message to the FastAPI backend.
 * @param {string} userText The message content from the user.
 * @param {string} sessionId The current session ID (defaulting to 'default').
 * @returns {Promise<string>} The AI response text.
 */
async function makeApiCall(userText, sessionId = "default") {
  const payload = {
    message: userText,
    session_id: sessionId,
  };

  try {
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMessage =
        errorData.error ||
        `Server Error: ${response.status} ${response.statusText}`;
      throw new Error(errorMessage);
    }

    const result = await response.json();

    // Asumsi respons dari FastAPI adalah { response: "AI text", session_id: "..." }
    if (result.response) {
      return result.response;
    } else {
      throw new Error(
        "Invalid response format from FastAPI backend (missing 'response' field)."
      );
    }
  } catch (error) {
    console.error("FastAPI call failed:", error);
    // Mengembalikan pesan error yang jelas kepada pengguna
    return `❌ **Kesalahan Koneksi:** Gagal menghubungi layanan AI. Cek apakah server FastAPI Anda berjalan dan end-point \`/api/chat\` berfungsi. Kesalahan: ${error.message}`;
  }
}

/**
 * Mengambil riwayat chat dari FastAPI dan menampilkannya.
 * @returns {Promise<boolean>} True jika riwayat dimuat, False jika kosong atau gagal.
 */
async function loadPreviousChat() {
  try {
    const response = await fetch(historyApiUrl);

    if (!response.ok) {
      // Throw error tapi tetap biarkan logic catch-nya mengembalikan false
      throw new Error(`Failed to load history: ${response.statusText}`);
    }

    const data = await response.json();
    const history = data.history || [];

    if (history.length > 0) {
      $chatHistoryContainer.empty();
      let lastUserMessage = "";

      // Tampilkan semua riwayat
      history.forEach((msg) => {
        appendMessage(msg.role, msg.content);
        if (msg.role === "user") {
          lastUserMessage = msg.content;
        }
      });

      // Update judul chat dengan pesan terakhir pengguna
      if (lastUserMessage) {
        const shortText =
          lastUserMessage.length > 30
            ? lastUserMessage.substring(0, 30) + "..."
            : lastUserMessage;
        $chatTitle.text(shortText);
      }

      // PENTING: Scroll ke bawah setelah semua pesan dimuat
      $conversationContainer.scrollTop($conversationContainer[0].scrollHeight);

      return true; // Riwayat berhasil dimuat
    }
    return false; // Riwayat kosong
  } catch (error) {
    console.error("Error loading previous chat:", error);
    return false; // Gagal memuat riwayat
  }
}

async function sendMessage() {
  if (isFetching || $chatInput.val().trim() === "") return;

  const userText = $chatInput.val().trim();
  const tempAiId = "ai-loading-" + Date.now();
  const currentSessionId = "default"; // Menggunakan ID sesi default untuk memuat memori default

  // 1. Reset UI and set fetching state
  $chatInput.val("");
  adjustTextareaHeight();
  isFetching = true;
  $sendButton.prop("disabled", true);

  // 2. Append User Message
  appendMessage("user", userText);
  // Riwayat tidak ditambahkan secara lokal; itu ditangani di backend (Orchestrator).

  // 3. Update chat title with first message
  if ($chatTitle.text() === "Obrolan AI Baru") {
    const shortText =
      userText.length > 30 ? userText.substring(0, 30) + "..." : userText;
    $chatTitle.text(shortText);
  }

  // 4. Append Loading Message
  const loadingMessage = `
    <div class="flex items-center space-x-2">
      <i data-lucide="loader-circle" class="w-5 h-5 animate-spin-slow text-blue-500"></i>
    </div>
  `;
  appendMessage("model", loadingMessage, tempAiId);

  // 5. Call API
  try {
    const aiResponseText = await makeApiCall(userText, currentSessionId);
    updateMessage(tempAiId, aiResponseText);
  } catch (error) {
    console.error("Fatal error during chat process:", error);
    updateMessage(
      tempAiId,
      `❌ **Kesalahan Fatal:** Tidak dapat memproses permintaan. Silakan coba lagi. (${error.message})`
    );
  } finally {
    // 6. Reset fetching state
    isFetching = false;
    // Re-enable send button if input is not empty
    if ($chatInput.val().trim() !== "") {
      $sendButton.prop("disabled", false);
    }
  }
}

// --- New Chat Functionality (Disederhanakan) ---
function startNewChat() {
  // Hapus: chatHistory.length = 0;
  $chatHistoryContainer.empty();

  $chatTitle.text("Obrolan AI Baru");

  // Add welcome message back
  const welcomeMessage = `
    <div class="flex justify-center text-center pt-8">
      <div class="max-w-lg p-6 rounded-xl bg-white dark:bg-gray-800 shadow-xl border border-gray-100 dark:border-gray-700/50">
        <i data-lucide="sparkles" class="w-8 h-8 mx-auto mb-3 text-blue-600 dark:text-blue-400"></i>
        <h2 class="text-xl font-bold mb-2">Halo! Saya Nano.</h2>
        <p class="text-gray-600 dark:text-gray-300">
          Tanyakan apapun yang Anda butuhkan: ide coding, analisis,
          penulisan esai, atau buatkan aplikasi web di editor di sebelah
          kanan.
        </p>
      </div>
    </div>
  `;
  $chatHistoryContainer.html(welcomeMessage);
  lucide.createIcons();

  $chatInput.val("");
  adjustTextareaHeight();
  $sendButton.prop("disabled", true);

  // Close sidebar on mobile after starting new chat
  if (window.innerWidth < 768) {
    toggleSidebar(false, true);
  }
}

// --- UI Interaction Handlers (Tidak Berubah) ---

// Toggle Sidebar
function toggleSidebar(forceOpen = false, forceClose = false) {
  const isHidden = $sidebar.hasClass("-translate-x-full");
  const isDesktop = window.innerWidth >= 768;

  let shouldOpen = forceOpen || (isHidden && !forceClose);
  let shouldClose = forceClose || (!isHidden && !forceOpen);

  if (shouldClose) {
    $sidebar.addClass("-translate-x-full");
    if (!isDesktop) {
      $overlay.addClass("opacity-0 pointer-events-none");
      $overlay.removeClass("opacity-50");
    }
    // Tampilkan tombol buka sidebar dan obrolan baru
    $openBtn.show();
    $newChatHeaderBtn.show();
    if (isDesktop) {
      $mainContent.removeClass("md:ml-64");
      // Tampilkan ikon header dengan menambahkan md:flex kembali
      $appIconHeader.addClass("md:flex");
    }
  } else if (shouldOpen) {
    $sidebar.removeClass("-translate-x-full");
    if (!isDesktop) {
      $overlay.removeClass("opacity-0 pointer-events-none");
      $overlay.addClass("opacity-50");
    }
    // Sembunyikan tombol buka sidebar dan obrolan baru karena sudah ada di sidebar
    $openBtn.hide();
    $newChatHeaderBtn.hide();
    $toggleIcon.attr("data-lucide", "chevrons-left"); // DIKEMBALIKAN ke 'chevrons-left'
    if (isDesktop) {
      $mainContent.addClass("md:ml-64");
      // Sembunyikan ikon header dengan menghapus md:flex
      $appIconHeader.removeClass("md:flex");
    }
  }
  lucide.createIcons();
}

// Inisialisasi Ikon Tema (Tema gelap sudah diset di <head>)
function initializeThemeIcon() {
  // Hapus SVG lama yang mungkin dibuat oleh pemanggilan otomatis Lucide
  $themeIcon.find("svg").remove();

  const isDark = $html.hasClass("dark");
  $themeIcon.attr("data-lucide", isDark ? "sun" : "moon");
  lucide.createIcons();
}

// Textarea Auto-Resize
function adjustTextareaHeight() {
  const chatInputDom = $chatInput[0];
  chatInputDom.style.height = "auto";
  const newHeight = Math.min(chatInputDom.scrollHeight, 150);
  chatInputDom.style.height = newHeight + "px";
}

// Set Initial Sidebar State
function setInitialSidebarState() {
  const isDesktop = window.innerWidth >= 768;
  if (isDesktop) {
    // Default: Sidebar DITUTUP (Closed)
    $sidebar.addClass("-translate-x-full"); // Pastikan sidebar tersembunyi
    $openBtn.show(); // Tampilkan tombol buka sidebar
    $newChatHeaderBtn.show(); // Tampilkan tombol obrolan baru
    $mainContent.removeClass("md:ml-64"); // Hapus margin pada konten utama
    // Tampilkan ikon aplikasi di header saat sidebar tertutup (desktop)
    $appIconHeader.addClass("md:flex");
  } else {
    // Mobile: Sidebar DITUTUP (Closed)
    $sidebar.addClass("-translate-x-full");
    $openBtn.show();
    $newChatHeaderBtn.show();
    $mainContent.removeClass("md:ml-64");
  }
  // Ikon tutup dipertahankan sebagai 'chevrons-left' dari HTML
  // Ikon buka tetap 'chevrons-right' (di header)
  lucide.createIcons();
}

// --- Document Ready / Initialization ---
$(document).ready(function () {
  // Event Listeners (Tidak Berubah)
  $toggleBtn.on("click", () => toggleSidebar(false, true));
  $openBtn.on("click", () => toggleSidebar(true, false));
  $overlay.on("click", () => toggleSidebar(false, true));

  $newChatSidebarBtn.on("click", (e) => {
    e.preventDefault();
    startNewChat();
  });

  $newChatHeaderBtn.on("click", (e) => {
    e.preventDefault();
    startNewChat();
  });

  $themeToggleBtn.on("click", () => {
    $html.toggleClass("dark");
    const isDark = $html.hasClass("dark");
    localStorage.setItem("theme", isDark ? "dark" : "light");

    // Hapus SVG lama sebelum mengganti atribut ikon
    $themeIcon.find("svg").remove();

    $themeIcon.attr("data-lucide", isDark ? "sun" : "moon");
    lucide.createIcons(); // Render ulang ikon baru
  });

  $chatInput.on("input", () => {
    adjustTextareaHeight();
    $sendButton.prop("disabled", isFetching || $chatInput.val().trim() === "");
  });

  $sendButton.on("click", sendMessage);

  $chatInput.on("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  });

  // Initial setup calls
  initializeThemeIcon();
  setInitialSidebarState();
  adjustTextareaHeight();
  // HAPUS PANGGILAN startNewChat() DI SINI: startNewChat();

  // LOGIKA BARU: Coba muat riwayat terakhir, jika gagal, mulai chat baru.
  loadPreviousChat().then((isLoaded) => {
    if (!isLoaded) {
      startNewChat(); // Panggil ini hanya jika tidak ada riwayat
    }
  });

  // Ensure sidebar state is handled on resize
  $(window).on("resize", setInitialSidebarState);

  // Focus input after a slight delay
  setTimeout(() => {
    $chatInput.focus();
  }, 500);
});
