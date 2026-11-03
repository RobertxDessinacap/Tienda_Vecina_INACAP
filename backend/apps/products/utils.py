import os
import uuid
from io import BytesIO
from PIL import Image
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
TARGET_WIDTH = 900
TARGET_HEIGHT = 600
MAX_FILE_SIZE_BYTES = 1024 * 1024  # Exactamente 1 MB

def process_and_secure_product_image(image_file):
    """
    Seguridad y Normalización de Imágenes para Productos (ISO 27001):
    1. Valida extensión permitida.
    2. Valida encabezado real (Magic Bytes) con Pillow para evitar ejecución de scripts maliciosos.
    3. Normaliza resolución exactamente a 900x600 con preservación de ratio y fondo neutro.
    4. Comprime dinámicamente para garantizar un peso máximo de 1 MB.
    """
    if not image_file:
        raise ValidationError("No se ha proporcionado ningún archivo de imagen.")

    # 1. Validación de Extensión
    name, ext = os.path.splitext(image_file.name)
    ext_lower = ext.lower()
    if ext_lower not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Extensión '{ext}' no permitida por seguridad. Solo se admiten: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 2. Verificación de Encabezado y Formato Real con Pillow
    try:
        image = Image.open(image_file)
        image.verify()  # Verifica integridad estructural del archivo
        # Reabrir ya que verify() deja el archivo en estado cerrado
        image_file.seek(0)
        image = Image.open(image_file)
    except Exception as e:
        raise ValidationError(f"El archivo subido no es una imagen válida o está dañado: {str(e)}")

    # 3. Conversión de Modo a RGB
    if image.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if 'A' in image.mode else None)
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')

    # 4. Ajuste Proporcional y Centrado a Resolución Exacta 900x600
    canvas = Image.new('RGB', (TARGET_WIDTH, TARGET_HEIGHT), (255, 255, 255))
    image.thumbnail((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)
    offset_x = (TARGET_WIDTH - image.width) // 2
    offset_y = (TARGET_HEIGHT - image.height) // 2
    canvas.paste(image, (offset_x, offset_y))

    # 5. Compresión Dinámica (Garantía <= 1 MB)
    quality = 90
    output_buffer = BytesIO()
    while quality >= 30:
        output_buffer.seek(0)
        output_buffer.truncate(0)
        canvas.save(output_buffer, format='JPEG', quality=quality, optimize=True)
        size = output_buffer.tell()
        if size <= MAX_FILE_SIZE_BYTES:
            break
        quality -= 10

    output_buffer.seek(0)
    secure_filename = f"prod_{uuid.uuid4().hex[:12]}.jpg"
    return ContentFile(output_buffer.read(), name=secure_filename)
