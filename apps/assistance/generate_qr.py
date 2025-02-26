import qrcode

from io import BytesIO
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import CircleModuleDrawer


def generate_qrcode(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    
    qr.add_data(data)
    img = qr.make_image(image_factory=StyledPilImage, module_drawer=CircleModuleDrawer())

    img_bytes_io = BytesIO()
    img.save(img_bytes_io, format='PNG')
    img_bytes = img_bytes_io.getvalue()

    return img_bytes