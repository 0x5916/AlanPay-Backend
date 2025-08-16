import qrcode
from io import BytesIO
import qrcode.image.pil


factory = qrcode.image.pil.PilImage

def create_qr_code(string: str) -> bytes:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(string)
    qr.make(fit=True)
    qr_code = qr.make_image(image_factory=factory)

    buffer = BytesIO()
    qr_code.save(buffer)
    return buffer.getvalue()
