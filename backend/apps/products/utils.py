import os
import uuid
from io import BytesIO
from PIL import Image
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

# Blindaje contra ataques de Denegación de Servicio por Decompression Bomb (Pixel Bombs)
Image.MAX_IMAGE_PIXELS = 10_000_000

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_FORMATS = {'JPEG', 'PNG', 'WEBP'}
TARGET_WIDTH = 900
TARGET_HEIGHT = 600
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB máximo de carga cruda antes de decodificar
MAX_FILE_SIZE_BYTES = 1024 * 1024    # Exactamente 1 MB de salida normalizada


def process_and_secure_product_image(image_file):
    """
    Seguridad y Normalización de Imágenes para Productos (ISO 27001):
    1. Valida tamaño bruto máximo de carga (<= 10 MB) antes de decodificar.
    2. Valida extensión permitida.
    3. Valida encabezado real (Magic Bytes) con Pillow para evitar ejecución de scripts maliciosos.
    4. Normaliza resolución exactamente a 900x600 con preservación de ratio y fondo neutro.
    5. Compresión acotada (máximo 2 pasadas: quality=85, fallback quality=65 si excede 1 MB).
    """
    if not image_file:
        raise ValidationError("No se ha proporcionado ningún archivo de imagen.")

    # 1. Guarda de tamaño máximo bruto antes de decodificar con Pillow
    file_size = getattr(image_file, 'size', None)
    if file_size is None and hasattr(image_file, 'seek') and hasattr(image_file, 'tell'):
        pos = image_file.tell()
        image_file.seek(0, os.SEEK_END)
        file_size = image_file.tell()
        image_file.seek(pos)

    if file_size is not None:
        if file_size == 0:
            raise ValidationError("El archivo de imagen está vacío.")
        if file_size > MAX_UPLOAD_BYTES:
            raise ValidationError(
                f"El archivo excede el tamaño máximo permitido de subida ({MAX_UPLOAD_BYTES // (1024 * 1024)} MB)."
            )

    # 2. Validación de Extensión
    _, ext = os.path.splitext(getattr(image_file, 'name', '') or '')
    ext_lower = ext.lower()
    if ext_lower not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Extensión '{ext}' no permitida por seguridad. Solo se admiten: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # 3. Verificación de Encabezado y Formato Real con Pillow
    try:
        image_file.seek(0)
        image = Image.open(image_file)
        if image.format not in ALLOWED_FORMATS:
            raise ValidationError(f"Formato real de imagen '{image.format}' no permitido por seguridad.")
        image.verify()  # Verifica integridad estructural del archivo
        # Reabrir ya que verify() deja el archivo en estado cerrado
        image_file.seek(0)
        image = Image.open(image_file)
        image.load()
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"El archivo subido no es una imagen válida o está dañado: {str(e)}")

    # 4. Conversión de Modo a RGB
    if image.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if 'A' in image.mode else None)
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')

    # 5. Ajuste Proporcional y Centrado a Resolución Exacta 900x600
    canvas = Image.new('RGB', (TARGET_WIDTH, TARGET_HEIGHT), (255, 255, 255))
    image.thumbnail((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)
    offset_x = (TARGET_WIDTH - image.width) // 2
    offset_y = (TARGET_HEIGHT - image.height) // 2
    canvas.paste(image, (offset_x, offset_y))

    # 6. Compresión acotada (quality=85, fallback quality=65 si > 1 MB)
    output_buffer = BytesIO()
    canvas.save(output_buffer, format='JPEG', quality=85, optimize=True)
    if output_buffer.tell() > MAX_FILE_SIZE_BYTES:
        output_buffer.seek(0)
        output_buffer.truncate(0)
        canvas.save(output_buffer, format='JPEG', quality=65, optimize=True)

    output_buffer.seek(0)
    secure_filename = f"prod_{uuid.uuid4().hex[:12]}.jpg"
    return ContentFile(output_buffer.read(), name=secure_filename)
