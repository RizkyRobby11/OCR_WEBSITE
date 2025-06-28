"""
Modul utama untuk Bot Telegram Konversi Gambar ke Excel.

File ini akan berisi:
- Inisialisasi bot.
- Handler untuk perintah (misalnya, /start).
- Handler untuk menerima pesan gambar.
- Alur kerja utama yang mengoordinasikan modul lain
  (image_processor, data_parser, excel_generator).
"""
import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import excel_generator
import camelot_processor
import image_processor

# Muat environment variables dari .env file
load_dotenv()

# Konfigurasi logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ambil token dari environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN tidak ditemukan di file .env")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mengirim pesan ketika perintah /start dijalankan."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Halo {user.mention_html()}! Kirimkan saya gambar yang berisi tabel, dan saya akan mencoba mengubahnya menjadi file Excel.",
    )


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menangani pesan gambar yang dikirim oleh pengguna."""
    # Pastikan direktori ada
    os.makedirs("temp_images", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    await update.message.reply_text(
        "Gambar diterima! Saya akan mulai memprosesnya. Ini mungkin memakan waktu beberapa saat..."
    )

    try:
        # Dapatkan objek file dari pesan
        photo_file = await update.message.photo[-1].get_file()
        
        # Buat path file sementara
        temp_image_path = os.path.join("temp_images", f"{photo_file.file_id}.jpg")

        # Unduh file
        await photo_file.download_to_drive(temp_image_path)
        logger.info(f"Gambar disimpan di: {temp_image_path}")

        # --- ALUR KERJA DIAGNOSTIK ---

        # 1. Panggil image_processor untuk mendeteksi area dan menggambar kotak
        logger.info(f"Memulai mode diagnostik untuk: {temp_image_path}")
        detected_count, diagnostic_path = image_processor.draw_detected_areas(temp_image_path)
        logger.info(f"Deteksi selesai. Ditemukan {detected_count} area.")

        # 2. Kirim gambar diagnostik kembali ke pengguna
        caption = f"Mode Diagnostik: Saya menemukan {detected_count} kemungkinan area tabel (ditandai dengan kotak merah). Silakan periksa apakah kotak ini sudah benar."
        
        await update.message.reply_photo(
            photo=open(diagnostic_path, 'rb'),
            caption=caption
        )

    except Exception as e:
        logger.error(f"Terjadi kesalahan: {e}", exc_info=True)
        await update.message.reply_text(f"Maaf, terjadi kesalahan saat memproses gambar: {e}")
    finally:
        # Hapus file sementara
        if 'temp_image_path' in locals():
            temp_pdf_path = temp_image_path.replace('.jpg', '.pdf')
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
                logger.info(f"File gambar sementara dihapus: {temp_image_path}")
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
                logger.info(f"File PDF sementara dihapus: {temp_pdf_path}")

        if 'diagnostic_path' in locals() and os.path.exists(diagnostic_path):
            os.remove(diagnostic_path)
            logger.info(f"File diagnostik sementara dihapus: {diagnostic_path}")


def main() -> None:
    """Memulai dan menjalankan bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Handler untuk perintah
    application.add_handler(CommandHandler("start", start))

    # Handler untuk pesan gambar
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))

    # Jalankan bot sampai pengguna menekan Ctrl-C
    logger.info("Bot starting...")
    application.run_polling()


if __name__ == "__main__":
    main()