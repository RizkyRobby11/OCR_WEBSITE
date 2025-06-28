"""
Modul untuk memproses gambar dan mengekstrak tabel menggunakan Camelot.
Engine ini mengonversi gambar ke PDF sementara sebelum diproses.
"""
import camelot
import pandas as pd
import os
from PIL import Image

def extract_tables_with_camelot(image_path: str, table_areas: list = None):
    """
    Mengekstrak tabel dari gambar, dengan panduan koordinat jika tersedia.

    Args:
        image_path: Path ke file gambar.
        table_areas: List berisi string koordinat, contoh: ['10,50,400,300'].

    Returns:
        Tuple berisi (pesan_status, daftar_dataframes).
    """
    pdf_path = ""
    try:
        # 1. Konversi Gambar ke PDF
        image = Image.open(image_path)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        pdf_path = image_path.replace('.jpg', '.pdf')
        image.save(pdf_path, "PDF", resolution=300.0) # Resolusi lebih tinggi

        # 2. Proses PDF dengan Camelot
        if table_areas:
            # Gunakan mode terpandu jika koordinat tersedia
            tables = camelot.read_pdf(pdf_path, flavor='lattice', table_areas=table_areas, pages='1')
            # Jika lattice gagal, coba stream pada area yang sama
            if tables.n == 0:
                tables = camelot.read_pdf(pdf_path, flavor='stream', table_areas=table_areas, pages='1')
            status_message = f"Mengekstrak {tables.n} tabel dari {len(table_areas)} area terdeteksi."
        else:
            # Fallback ke mode otomatis jika tidak ada koordinat
            tables = camelot.read_pdf(pdf_path, flavor='lattice', pages='1')
            if tables.n == 0:
                tables = camelot.read_pdf(pdf_path, flavor='stream', pages='1')
            status_message = f"Mode otomatis menemukan {tables.n} tabel."

        # 3. Ambil DataFrame dari setiap tabel
        dataframes = [table.df for table in tables]
        
        return status_message, dataframes

    except Exception as e:
        error_message = f"Terjadi kesalahan saat menggunakan Camelot: {e}"
        return error_message, []
    finally:
        # 4. Hapus file PDF sementara
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
