import qrcode


def generate_qr(data):
    # Crear el código QR con la biblioteca qrcode
    qr = qrcode.QRCode(version=1, box_size=10, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Cambiar el tamaño de la imagen con la biblioteca Pillow
    new_size = (300, 300)
    qr_img = qr_img.resize(new_size)

    # Guardar la imagen en un archivo
    # qr_img.save("codigoQR.png")

    return qr_img
