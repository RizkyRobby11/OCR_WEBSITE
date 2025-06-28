"""
Modul untuk deteksi lokasi tabel menggunakan OpenCV.
Tujuannya adalah untuk menemukan koordinat tabel dan memberikannya ke Camelot.
"""
import cv2
import numpy as np

def draw_detected_areas(image_path: str):
    """
    Mendeteksi sel-sel individual dalam tabel dan menggambar kotak di sekelilingnya.

    Args:
        image_path: Path ke file gambar asli.

    Returns:
        Tuple: (jumlah sel terdeteksi, path ke gambar diagnostik).
    """
    image = cv2.imread(image_path)
    if image is None:
        return 0, image_path

    diagnostic_image = image.copy()

    # 1. Pra-pemrosesan
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(~gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, -2)

    # 2. Isolasi Garis Horizontal & Vertikal (dengan parameter yang lebih halus)
    horizontal = binary.copy()
    vertical = binary.copy()
    scale = 30  # Sedikit lebih kecil untuk mendeteksi garis yang lebih pendek

    horizontal_size = horizontal.shape[1] // scale
    horizontal_structure = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_size, 1))
    cv2.erode(horizontal, horizontal_structure, iterations=1, dst=horizontal)
    cv2.dilate(horizontal, horizontal_structure, iterations=1, dst=horizontal)

    vertical_size = vertical.shape[0] // scale
    vertical_structure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vertical_size))
    cv2.erode(vertical, vertical_structure, iterations=1, dst=vertical)
    cv2.dilate(vertical, vertical_structure, iterations=1, dst=vertical)

    # 3. Buat kerangka tabel
    table_mask = cv2.add(horizontal, vertical)

    # 4. Temukan kontur DARI DALAM kerangka untuk mengidentifikasi sel
    #    Kita gunakan RETR_TREE untuk mendapatkan semua kontur dan hierarkinya
    contours, _ = cv2.findContours(table_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    detected_count = 0
    for contour in contours:
        # Filter kontur berdasarkan area untuk mendapatkan sel yang valid
        if cv2.contourArea(contour) > 100:
            detected_count += 1
            x, y, w, h = cv2.boundingRect(contour)
            # Gambar kotak hijau di sekitar setiap sel
            cv2.rectangle(diagnostic_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Simpan gambar diagnostik
    diagnostic_path = image_path.replace('.jpg', '_diagnostic.jpg')
    cv2.imwrite(diagnostic_path, diagnostic_image)

    return detected_count, diagnostic_path