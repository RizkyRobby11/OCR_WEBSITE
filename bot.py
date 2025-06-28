"""
Modul utama untuk Bot Telegram Konversi Gambar ke Excel.
Arsitektur baru menggunakan 'img2table' untuk ekstraksi lokal yang andal.
"""
import logging
import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

import excel_generator
import table_extractor # Modul baru yang menggunakan 'img2table'

# Muat environment variables dari .env file
load_dotenv()

# Konfigurasi logging dasar
logging.basicConfig(
    format="%(asctime)s - %(name)s - [%(levelname)s] - %(message)s", level=logging.INFO
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
        rf"Halo {user.mention_html()}! Kirimkan gambar tabel. Saya akan mengekstraknya menjadi file Excel menggunakan pemrosesan lokal yang canggih.",
    )

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menangani pesan gambar, memberikan umpan balik instan, dan memulai proses di latar belakang."""
    os.makedirs("temp_images", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    chat_id = update.effective_chat.id
    photo_file = await update.message.photo[-1].get_file()
    temp_image_path = os.path.join("temp_images", f"{photo_file.file_id}.jpg")
    await photo_file.download_to_drive(temp_image_path)
    logger.info(f"Gambar disimpan di: {temp_image_path}")

    # Kirim pesan konfirmasi instan
    await context.bot.send_message(
        chat_id=chat_id,
        text="✅ Gambar diterima. Memulai analisis lokal di latar belakang. "
             "Proses ini bisa memakan waktu, terutama saat pertama kali. "
             "Saya akan mengirimkan file Excel jika sudah selesai."
    )

    # Jalankan proses yang berat di thread terpisah untuk tidak memblokir bot
    context.application.create_task(
        process_image_in_background(context, chat_id, temp_image_path)
    )

async def process_image_in_background(context: ContextTypes.DEFAULT_TYPE, chat_id: int, temp_image_path: str):
    """Fungsi yang berjalan di latar belakang untuk memproses gambar."""
    output_excel_path = None
    try:
        logger.info(f"Memulai pemrosesan latar belakang untuk: {temp_image_path}")
        
        # Jalankan fungsi ekstraksi lokal yang memblokir di thread terpisah
        dataframes = await asyncio.to_thread(
            table_extractor.extract_tables_from_image_local,
            temp_image_path
        )

        if not dataframes:
            await context.bot.send_message(chat_id=chat_id, text="Analisis selesai. Maaf, tidak ada tabel yang dapat diekstrak dari gambar ini.")
            return

        logger.info(f"Berhasil mengekstrak {len(dataframes)} tabel.")
        await context.bot.send_message(chat_id=chat_id, text=f"Analisis selesai! Menyusun {len(dataframes)} tabel yang ditemukan ke dalam file Excel...")

        output_excel_path = os.path.join("output", f"hasil_{os.path.basename(temp_image_path).split('.')[0]}.xlsx")
        # Untuk img2table, kita tidak punya teks ringkasan terpisah, jadi kita kirim string kosong
        final_excel_path = excel_generator.create_excel_file(
            dataframes=dataframes,
            summary_text="", 
            output_path=output_excel_path
        )

        if final_excel_path:
            logger.info(f"File Excel berhasil dibuat di: {final_excel_path}")
            await context.bot.send_message(chat_id=chat_id, text="Selesai! Ini dia file Excel hasil rekonstruksi.")
            await context.bot.send_document(chat_id=chat_id, document=open(final_excel_path, 'rb'))
        else:
            await context.bot.send_message(chat_id=chat_id, text="Maaf, tidak dapat membuat file Excel. Mungkin tidak ada tabel yang valid ditemukan.")

    except Exception as e:
        logger.error(f"Terjadi kesalahan besar dalam alur kerja latar belakang: {e}", exc_info=True)
        await context.bot.send_message(chat_id=chat_id, text=f"Maaf, terjadi kesalahan yang tidak terduga saat memproses gambar: {e}")
    finally:
        # Hapus semua file sementara
        files_to_delete = [temp_image_path, output_excel_path]
        for file_path in files_to_delete:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File sementara dihapus: {file_path}")

def main() -> None:
    """Memulai dan menjalankan bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    
    print("="*50)
    print("INFO: Bot berhasil dimulai dan siap menerima gambar.")
    print("="*50)
    logger.info("Bot starting polling...")
    application.run_polling()

if __name__ == "__main__":
    main()