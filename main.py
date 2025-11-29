# main.py

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from app.memory.base_memory import BaseMemory

# Impor komponen utama Anda
from app.core.orchestrator import Orchestrator
from app.utils.logger import logger

# Inisialisasi FastAPI
app = FastAPI(title="Nano AI Agent")

# Konfigurasi untuk UI (Templates dan Static Files)
# Memasang direktori 'static'
app.mount("/static", StaticFiles(directory="app/ui/static"), name="static")
# Memuat direktori 'templates'
templates = Jinja2Templates(directory="app/ui/templates")

# Inisialisasi Orchestrator (asumsi ini adalah kelas utama yang menangani logika)
try:
    orchestrator = Orchestrator()
    logger.info("Orchestrator AI berhasil diinisialisasi.")
except Exception as e:
    logger.error(f"Gagal menginisialisasi Orchestrator: {e}")
    orchestrator = None

memory_loader = BaseMemory()


# Pydantic model untuk respon riwayat chat
class ChatHistoryResponse(BaseModel):
    history: list[dict]


# --- Skema Data untuk Input Chat ---
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"  # Menggunakan ID default untuk memuat memori default


# --- ENDPOINTS UI (HTML) ---


@app.get("/api/history")
def get_chat_history():
    """Mengambil seluruh riwayat chat yang tersimpan."""
    try:
        raw_history = memory_loader.load_all_memory()

        # Konversi format memory ke format yang dapat digunakan di front-end
        # Format memory: list[dict(user, assistant, actions)]
        # Format front-end: list[dict(role, content)]

        formatted_history = []
        for record in raw_history:
            # 1. Pesan Pengguna
            if record.get("user"):
                formatted_history.append({"role": "user", "content": record["user"]})

            # 2. Pesan Asisten (termasuk output tool/actions jika ada)
            assistant_response = record.get("assistant")
            if assistant_response:
                # TODO: Jika Anda ingin menampilkan tool/action output di UI,
                # Anda harus memformatnya di sini sebelum pesan asisten.
                formatted_history.append(
                    {"role": "model", "content": assistant_response}
                )

        return {"history": formatted_history}

    except Exception as e:
        logger.error(f"Error loading history: {e}")
        return {"history": []}


@app.get("/", response_class=HTMLResponse)
async def serve_chat_interface(request: Request):
    """Menyajikan halaman HTML antarmuka chat."""
    # Anda mungkin perlu meneruskan beberapa variabel ke template di sini
    return templates.TemplateResponse(
        "index.html", {"request": request, "app_name": "Nano"}
    )


# --- ENDPOINTS API (Chat) ---


@app.post("/api/chat")
async def handle_chat_message(chat_request: ChatRequest):
    """Menerima pesan chat dan mengembalikan respons AI."""
    if not orchestrator:
        return {"error": "Layanan AI tidak tersedia."}, 503

    try:
        # Panggil Orchestrator DENGAN FUNGSI YANG BENAR
        ai_response_text = orchestrator.process_message(
            prompt=chat_request.message,  # Ganti 'user_input' menjadi 'prompt' (sesuai definisi di orchestrator.py)
            session_id=chat_request.session_id,
        )

        # PASTIKAN PENGEMBALIAN MEMILIKI KUNCI "response"
        return {"response": ai_response_text, "session_id": chat_request.session_id}

    except Exception as e:
        # log error di backend
        logger.error(f"Kesalahan pemrosesan chat: {e}")
        # Kembalikan error yang ramah ke front-end
        return {"error": f"Kesalahan internal server: {e}"}, 500


# Untuk menjalankan aplikasi ini: uvicorn main:app --reload
