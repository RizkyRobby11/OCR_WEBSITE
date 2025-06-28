"""
Modul inti baru yang menggunakan 'img2table' untuk ekstraksi tabel yang andal.
"""
from img2table.document import Image
from img2table.ocr import EasyOCR
import pandas as pd

def extract_tables_from_image_local(image_path: str) -> list[pd.DataFrame]:
    """
    Mengekstrak tabel dari gambar menggunakan library img2table dengan backend EasyOCR.

    Args:
        image_path: Path ke file gambar.

    Returns:
        Daftar pandas DataFrame, di mana setiap DataFrame adalah tabel yang ditemukan.
    """
    try:
        # Inisialisasi OCR engine (EasyOCR)
        # Kita bisa menentukan bahasa di sini jika diperlukan
        ocr = EasyOCR(lang=["en", "id"])

        # Buat objek dokumen dari gambar
        doc = Image(src=image_path)

        # Ekstrak tabel
        # implicit_rows=True sangat penting untuk tabel tanpa garis horizontal yang jelas
        extracted_tables = doc.extract_tables(ocr=ocr,
                                              implicit_rows=True,
                                              borderless_tables=True)

        # Konversi hasil ke dalam format yang kita inginkan (list of DataFrames)
        dataframes = []
        for table in extracted_tables:
            dataframes.append(table.df)
        
        return dataframes

    except Exception as e:
        print(f"Error saat memproses dengan img2table: {e}")
        return []