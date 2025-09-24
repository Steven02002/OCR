import cv2
import pytesseract
import re
import os

# Configura la ruta a Tesseract (ejemplo para Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\ASUS\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
tessdata_dir_config = r'--tessdata-dir C:\Users\ASUS\AppData\Local\Programs\Tesseract-OCR\tessdata'

def limpiar_y_convertir_numero(texto_numero):
    """Limpia una cadena de número y la convierte a float."""
    texto_limpio = texto_numero.replace(',', '.')
    return float(re.sub(r'[^\d.]', '', texto_limpio))

def procesar_factura(texto):
    """Procesa el texto de una factura para verificar el total."""

    # 1. Encontrar la sección SUMMARY
    summary_match = re.search(r'SUMMARY', texto, re.IGNORECASE)
    if not summary_match:
        return "🤷‍♂️ No se pudo encontrar la sección 'SUMMARY' en la factura."
    
    texto_resumen = texto[summary_match.start():]
    texto_resumen = re.sub(r'[\t\n\r]+', ' ', texto_resumen)
    texto_resumen = re.sub(r'\s{2,}', ' ', texto_resumen)

    #print("🔎 Texto aislado de item:\n", texto_resumen[:400])  # Debug
    # 2. Extraer el total de Gross worth (último valor)
    gross_worth_total_matches = re.findall(
        r'Gross wort[h]?.*?\b([\d,.]*[,.]\d{2})\b',
        texto_resumen,
        re.IGNORECASE
    )
    if not gross_worth_total_matches:
        return "🤷‍♂️ No se pudo encontrar el 'Gross worth' final en la sección SUMMARY."
    
    total_en_factura = limpiar_y_convertir_numero(gross_worth_total_matches[-1])

    # 3. Extraer todos los valores intermedios de Gross worth (los ítems)
    gross_worth_items_matches = re.findall(
        r'Gross wort[h]?.*?((?:\d{1,3}[.,]\d{2}(?:\s+|$))+)',
        texto_resumen,
        re.IGNORECASE
    )

    if not gross_worth_items_matches:
        return f"🤷‍♂️ Se encontró un total de {total_en_factura:.2f}, pero no se encontraron valores de 'Gross worth' para sumar."

    # Tomamos el último bloque encontrado (porque a veces OCR repite encabezados)
    bloque = gross_worth_items_matches[-1]

    # Extraemos todos los números del bloque
    valores_lineas = re.findall(r'\b[\d,.]*[,.]\d{2}\b', bloque)

    if not valores_lineas:
        return f"🤷‍♂️ No se pudieron extraer valores de 'Gross worth' en la sección SUMMARY."

    # 4. Convertir y sumar
    total_calculado = sum(limpiar_y_convertir_numero(v) for v in valores_lineas)

    # 5. Comparar
    if abs(total_calculado - total_en_factura) < 0.05:
        return f"✅ El monto total de la factura es correcto: {total_en_factura:.2f}. La suma de los ítems ({total_calculado:.2f}) coincide."
    else:
        return f"❌ El monto total es incorrecto. La suma de los ítems es: {total_calculado:.2f}, pero el total en factura es: {total_en_factura:.2f}."


def identificar_documento(ruta_imagen):
    """Identifica el tipo de documento y llama a la función de procesamiento adecuada."""
    imagen = cv2.imread(ruta_imagen)
    if imagen is None:
        return "Error: No se pudo cargar la imagen. Verifique la ruta del archivo."

    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    umbral = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    texto = pytesseract.image_to_string(umbral, lang='eng', config=tessdata_dir_config)

    if "Invoice" in texto or "SUMMARY" in texto:
        print("🔍 Documento identificado como una factura.")
        print(procesar_factura(texto))
    else:
        print("🤷‍♂️ No se pudo identificar el tipo de documento.")

# --- Bloque de ejecución principal ---
if __name__ == "__main__":
    ruta_carpeta = r'C:\Users\ASUS\Documents\Tecnologias Emergentes\Prueba escrita\batch1_1'
    
    if not os.path.exists(ruta_carpeta):
        print(f"Error: La carpeta '{ruta_carpeta}' no existe.")
    else:
        for nombre_archivo in os.listdir(ruta_carpeta):
            ruta_completa = os.path.join(ruta_carpeta, nombre_archivo)
            
            if ruta_completa.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff')):
                print(f"\n--- Procesando archivo: {nombre_archivo} ---")
                identificar_documento(ruta_completa)
            else:
                print(f"Saltando archivo no compatible: {nombre_archivo}")