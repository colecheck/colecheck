import decimal
import json
import os
import tempfile
from http import HTTPStatus

import reportlab
import io
from datetime import datetime, timedelta, date
from io import BytesIO

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.colors import Color, black, white
from reportlab.lib.pagesizes import landscape, A5, portrait, A6, A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, TableStyle, Spacer, Image, Flowable
from reportlab.platypus import Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode import qr
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.units import cm, inch
from reportlab.rl_settings import defaultPageSize
from reportlab.lib import colors, utils

from apps.assistance.generate_qr import generate_qrcode
from apps.school.models import Classroom, Section, Grade
from apps.student.models import Student
from schoolAssistance import settings

PAGE_HEIGHT = defaultPageSize[1]
PAGE_WIDTH = defaultPageSize[0]

COLOR_PDF = colors.Color(red=(152.0 / 255), green=(29.0 / 255), blue=(31.0 / 255))
COLOR_GREEN = colors.Color(red=(27.0 / 255), green=(140.0 / 255), blue=(66.0 / 255))

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT, leading=30, fontName='NotoSerif-Regular', fontSize=25))
styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, leading=8, fontName='NotoSerif-Regular', fontSize=8))
styles.add(
    ParagraphStyle(name='JustifySquare', alignment=TA_JUSTIFY, leading=12, fontName='NotoSerif-Regular', fontSize=8))
styles.add(ParagraphStyle(name='LeftSquare', alignment=TA_LEFT, leading=12, fontName='NotoSerif-Regular', fontSize=13))
styles.add(
    ParagraphStyle(name='LeftSquareSmall', alignment=TA_LEFT, leading=9, fontName='NotoSerif-Regular', fontSize=10))
styles.add(
    ParagraphStyle(name='LeftSquareSmall2', alignment=TA_LEFT, leading=9, fontName='NotoSerif-Regular', fontSize=8))
styles.add(ParagraphStyle(name='Justify-Dotcirful', alignment=TA_JUSTIFY, leading=12, fontName='Dotcirful-Regular',
                          fontSize=10))
styles.add(
    ParagraphStyle(name='Justify-Dotcirful-table', alignment=TA_JUSTIFY, leading=12, fontName='Dotcirful-Regular',
                   fontSize=7))
styles.add(ParagraphStyle(name='Justify_Bold', alignment=TA_JUSTIFY, leading=8, fontName='Square-Bold', fontSize=8))

styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, leading=10, fontName='Square-Bold', fontSize=10,
                          textColor=COLOR_PDF))
styles.add(ParagraphStyle(name='Center-fecha', alignment=TA_CENTER, leading=10, fontName='Square-Bold', fontSize=10,
                          textColor=colors.black))
styles.add(ParagraphStyle(name='Center-datos', alignment=TA_CENTER, leading=10, fontName='Square', fontSize=10,
                          textColor=colors.black))
styles.add(ParagraphStyle(name='Center-arequipa', alignment=TA_CENTER, leading=19, fontName='Square-Bold', fontSize=10,
                          textColor=COLOR_PDF))
# styles.add(ParagraphStyle(name='Center-titulo', alignment=TA_CENTER, leading=20, fontName='Square-Bold', fontSize=20,
#                          textColor=colors.steelblue))
styles.add(ParagraphStyle(name='Center-titulo', alignment=TA_CENTER, leading=40, fontName='Square-Bold', fontSize=40,
                          textColor=colors.black))
styles.add(ParagraphStyle(name='Center-recibo', alignment=TA_CENTER, leading=20, fontName='Square-Bold', fontSize=20,
                          textColor=colors.white))
styles.add(ParagraphStyle(name='Center-id', alignment=TA_CENTER, leading=40, fontName='Lucida-Console', fontSize=30,
                          textColor=colors.black))
styles.add(ParagraphStyle(name='Center-ng', alignment=TA_CENTER, leading=10, fontName='Square-Bold', fontSize=10,
                          textColor=colors.white))
styles.add(
    ParagraphStyle(name='Left', alignment=TA_CENTER, leading=30, fontName='NotoSerif-Regular', fontSize=15,
                   textColor=colors.black))
styles.add(
    ParagraphStyle(name='Left-Simple', alignment=TA_LEFT, leading=15, fontName='NotoSerif-Regular', fontSize=15,
                   textColor=colors.black))
styles.add(ParagraphStyle(name='Left-name', alignment=TA_LEFT, leading=8, fontName='NotoSerif-Regular', fontSize=8,
                          textColor=COLOR_PDF))
styles.add(ParagraphStyle(name='Left-datos', alignment=TA_LEFT, leading=10, fontName='Square-Bold', fontSize=10,
                          textColor=colors.black))

styles.add(ParagraphStyle(name='Center4', alignment=TA_CENTER, leading=12, fontName='Square-Bold',
                          fontSize=14, spaceBefore=6, spaceAfter=6))
styles.add(ParagraphStyle(name='Center5', alignment=TA_LEFT, leading=15, fontName='ticketing.regular',
                          fontSize=12))
styles.add(
    ParagraphStyle(name='Center-Dotcirful', alignment=TA_CENTER, leading=12, fontName='Dotcirful-Regular', fontSize=10))
styles.add(ParagraphStyle(name='CenterTitle', alignment=TA_CENTER, leading=8, fontName='Square-Bold', fontSize=8))
styles.add(ParagraphStyle(name='CenterTitle-Dotcirful', alignment=TA_CENTER, leading=12, fontName='Dotcirful-Regular',
                          fontSize=10))
styles.add(ParagraphStyle(name='CenterTitle2', alignment=TA_CENTER, leading=8, fontName='Square-Bold', fontSize=12))
styles.add(ParagraphStyle(name='Center_Regular', alignment=TA_CENTER, leading=8, fontName='Ticketing', fontSize=10))
styles.add(ParagraphStyle(name='Center_Bold', alignment=TA_CENTER,
                          leading=8, fontName='Square-Bold', fontSize=12, spaceBefore=6, spaceAfter=6))
styles.add(ParagraphStyle(name='ticketing.regular', alignment=TA_CENTER,
                          leading=8, fontName='ticketing.regular', fontSize=14, spaceBefore=6, spaceAfter=6))
styles.add(ParagraphStyle(name='Center2', alignment=TA_CENTER, leading=8, fontName='Ticketing', fontSize=8))
styles.add(ParagraphStyle(name='Center3', alignment=TA_JUSTIFY, leading=8, fontName='Ticketing', fontSize=6))
style = styles["Normal"]

reportlab.rl_config.TTFSearchPath.append(str(settings.BASE_DIR) + '/static/fonts')
pdfmetrics.registerFont(TTFont('NotoSerif-Bold', 'NotoSerif-Bold.ttf'))
pdfmetrics.registerFont(TTFont('NotoSerif-Regular', 'NotoSerif-Regular.ttf'))
pdfmetrics.registerFont(TTFont('SourceSerifPro-Regular', 'SourceSerifPro-Regular.ttf'))
# pdfmetrics.registerFont(TTFont('Narrow', 'Arial Narrow.ttf'))
# pdfmetrics.registerFont(TTFont('Square', 'square-721-condensed-bt.ttf'))
# pdfmetrics.registerFont(TTFont('Square-Bold', 'sqr721bc.ttf'))
# pdfmetrics.registerFont(TTFont('Newgot', 'newgotbc.ttf'))
# pdfmetrics.registerFont(TTFont('Ticketing', 'ticketing.regular.ttf'))
# pdfmetrics.registerFont(TTFont('Lucida-Console', 'lucida-console.ttf'))
# pdfmetrics.registerFont(TTFont('Square-Dot', 'square_dot_digital-7.ttf'))
# pdfmetrics.registerFont(TTFont('Serif-Dot', 'serif_dot_digital-7.ttf'))
# pdfmetrics.registerFont(TTFont('Enhanced-Dot-Digital', 'enhanced-dot-digital-7.regular.ttf'))
# pdfmetrics.registerFont(TTFont('Merchant-Copy-Wide', 'MerchantCopyWide.ttf'))
# pdfmetrics.registerFont(TTFont('Dot-Digital', 'dot_digital-7.ttf'))
# pdfmetrics.registerFont(TTFont('Raleway-Dots-Regular', 'RalewayDotsRegular.ttf'))
# pdfmetrics.registerFont(TTFont('Ordre-Depart', 'Ordre-de-Depart.ttf'))
# pdfmetrics.registerFont(TTFont('Dotcirful-Regular', 'DotcirfulRegular.otf'))
# pdfmetrics.registerFont(TTFont('Nationfd', 'Nationfd.ttf'))
# pdfmetrics.registerFont(TTFont('Kg-Primary-Dots', 'KgPrimaryDots-Pl0E.ttf'))
# pdfmetrics.registerFont(TTFont('Dot-line', 'Dotline-LA7g.ttf'))
# pdfmetrics.registerFont(TTFont('Dot-line-Light', 'DotlineLight-XXeo.ttf'))
# pdfmetrics.registerFont(TTFont('Jd-Lcd-Rounded', 'JdLcdRoundedRegular-vXwE.ttf'))
# pdfmetrics.registerFont(TTFont('ticketing.regular', 'ticketing.regular.ttf'))
# pdfmetrics.registerFont(TTFont('allerta_medium', 'allerta_medium.ttf'))
# pdfmetrics.registerFont(TTFont('Romanesque_Serif', 'Romanesque Serif.ttf'))


MONTH = (
    "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE",
    "DICIEMBRE"
)

GRADE_DIC = {
    '1': 'Primero',
    '2': 'Segundo',
    '3': 'Tercero',
    '4': 'Cuarto',
    '5': 'Quinto',
    '6': 'Sexto'
}

LEVEL_DIC = {
    'I': 'Inicial',
    'P': 'Primaria',
    'S': 'Secundaria'
}


def qr_code(table):
    # generate and rescale QR
    qr_code = qr.QrCodeWidget(table)
    bounds = qr_code.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    drawing = Drawing(
        # 3.5 * cm, 3.5 * cm, transform=[3.5 * cm / width, 0, 0, 3.5 * cm / height, 0, 0])
        1 * cm, 1 * cm, transform=[4.5 * cm / width, 0, 0, 4.5 * cm / height, 0, 0])
    drawing.add(qr_code)

    return drawing


BASE = 21
ALTURA = 29.7


def encrypt_data(text, key):
    list_of_chars = ['á', 'Á', 'é', 'É', 'í', 'Í', 'ó', 'Ó', 'ú', 'Ú', 'ñ', 'Ñ']
    encrypted_text = ''
    for char in text:
        if char in list_of_chars:
            encrypted_text += char
        elif char.isalnum():
            if char.isalpha():
                start = ord('a') if char.islower() else ord('A')
                encrypted_text += chr((ord(char) - start + key) % 26 + start)
            else:
                encrypted_text += chr((ord(char) - ord('0') + key) % 10 + ord('0'))
        else:
            encrypted_text += char

    return encrypted_text


def create_qr_pdf_from_students(request, slug, section_id, grade_id):
    _wt = BASE * inch - 10 * 0.05 * inch

    ml = 0.0 * inch
    mr = 0.0 * inch
    ms = 0.039 * inch
    mi = 0.039 * inch

    _dictionary = []

    section = get_object_or_404(Section, id=section_id)
    students = list(section.students.all())

    style_table_1 = [
        ('BOX', (0, 0), (-1, -1), 2, colors.white),
        ('BOX', (0, 1), (-1, -1), 2, colors.white),
        # ('SPAN', (0, 0), (-1, 0)),
        # ('SPAN', (0, 1), (1, 1)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        # ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        # ('BOTTOMPADDING', (0, 0), (0, 0), -15),
        # ('LEFTPADDING', (0, 0), (0, 0), 60),
        # ('LEFTPADDING', (0, 1), (0, -1), 20),
    ]

    lenght_students = len(students)

    ana_c1 = ''
    ana_c2 = ''
    ana_c3 = ''
    ana_c4 = ''

    if True:
        for i in range(0, lenght_students, 4):
            if i < lenght_students:
                student = students[i]

                first_name_data = str(student.first_name)
                last_name_data = str(student.last_name)
                code = str(student.dni)
                level_data = str(student.level.name)
                grade_data = student.grade.short_name
                section_data = student.section.name

                data = f'{first_name_data}${last_name_data}${code}${grade_data}${section_data}'

                data_encrypt = encrypt_data(data, 3)

                qr_image_bytes = generate_qrcode(data=data_encrypt)

                # Crear un archivo temporal para guardar la imagen QR
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                    tmp_file.write(qr_image_bytes)
                    tmp_file_path = tmp_file.name

                # Crear la imagen usando ReportLab Image desde el archivo temporal
                image_data = Image(tmp_file_path)

                image_data.drawHeight = inch * 4
                image_data.drawWidth = inch * 4

                p1_1 = Paragraph(f'Nombre:', styles["Right"])
                p1_2 = Paragraph(f'{first_name_data.split()[0]} {last_name_data.split()[0]}', styles["Left"])
                p1_3 = Paragraph(f'Apellido:', styles["Right"])
                p1_4 = Paragraph(f'{last_name_data}', styles["Left"])
                p1_5 = Paragraph(f'DNI:', styles["Right"])
                p1_6 = Paragraph(f'{code}', styles["Left"])
                p1_7 = Paragraph(f'Grado:', styles["Right"])
                p1_8 = Paragraph(f'{grade_data}', styles["Left"])
                p1_9 = Paragraph(f'Sección:', styles["Right"])
                p1_10 = Paragraph(f'{section_data}', styles["Left"])

                # colwiths_table_1 = [_wt * 100 / 100 * 0.235]
                # rowwiths_table_1 = [inch * 4, inch * 0.5, inch * 0.5, inch * 0.5, inch * 0.5, inch * 0.5]
                ana_c1 = Table(
                    [(image_data,)] +
                    [(p1_2,)], )
                ana_c1.setStyle(TableStyle(style_table_1))

            # -------------------------------------------------------------------------------------------------- #
            # -------------------------------------------------------------------------------------------------- #
            if i + 1 < lenght_students:
                student = students[i + 1]
                first_name_data = str(student.first_name)
                last_name_data = str(student.last_name)
                code = str(student.dni)
                level_data = str(student.level.name)
                grade_data = student.grade.short_name
                section_data = student.section.name

                data = f'{first_name_data}${last_name_data}${code}${grade_data}${section_data}'

                data_encrypt = encrypt_data(data, 3)

                qr_image_bytes = generate_qrcode(data=data_encrypt)
                # Crear un archivo temporal para guardar la imagen QR
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                    tmp_file.write(qr_image_bytes)
                    tmp_file_path = tmp_file.name

                # Crear la imagen usando ReportLab Image desde el archivo temporal
                image_data = Image(tmp_file_path)

                image_data.drawHeight = inch * 4
                image_data.drawWidth = inch * 4

                p2_1 = Paragraph(f'Nombre:', styles["Right"])
                p2_2 = Paragraph(f'{first_name_data.split()[0]} {last_name_data.split()[0]}', styles["Left"])
                p2_3 = Paragraph(f'Apellido:', styles["Right"])
                p2_4 = Paragraph(f'{last_name_data}', styles["Left"])
                p2_5 = Paragraph(f'DNI:', styles["Right"])
                p2_6 = Paragraph(f'{code}', styles["Left"])
                p2_7 = Paragraph(f'Grado:', styles["Right"])
                p2_8 = Paragraph(f'{grade_data}', styles["Left"])
                p2_9 = Paragraph(f'Sección:', styles["Right"])
                p2_10 = Paragraph(f'{section_data}', styles["Left"])

                # colwiths_table_2 = [_wt * 40 / 100 * 0.32, _wt * 5 / 100 * 0.32, _wt * 55 / 100 * 0.32]
                # rowwiths_table_2 = [inch * 4, inch * 0.5, inch * 0.5, inch * 0.5, inch * 0.5, inch * 0.5]
                ana_c2 = Table(
                    [(image_data,)] +
                    [(p2_2,)],
                )
                ana_c2.setStyle(TableStyle(style_table_1))

            # -------------------------------------------------------------------------------------------------- #
            # -------------------------------------------------------------------------------------------------- #
            if i + 2 < lenght_students:
                student = students[i + 2]
                first_name_data = str(student.first_name)
                last_name_data = str(student.last_name)
                code = str(student.dni)
                level_data = str(student.level.name)
                grade_data = student.grade.short_name
                section_data = student.section.name

                data = f'{first_name_data}${last_name_data}${code}${grade_data}${section_data}'

                data_encrypt = encrypt_data(data, 3)

                qr_image_bytes = generate_qrcode(data=data_encrypt)
                # Crear un archivo temporal para guardar la imagen QR
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                    tmp_file.write(qr_image_bytes)
                    tmp_file_path = tmp_file.name

                # Crear la imagen usando ReportLab Image desde el archivo temporal
                image_data = Image(tmp_file_path)

                image_data.drawHeight = inch * 4
                image_data.drawWidth = inch * 4

                p3_1 = Paragraph(f'Nombre:', styles["Right"])
                p3_2 = Paragraph(f'{first_name_data.split()[0]} {last_name_data.split()[0]}', styles["Left"])
                p3_3 = Paragraph(f'Apellido:', styles["Right"])
                p3_4 = Paragraph(f'{last_name_data}', styles["Left"])
                p3_5 = Paragraph(f'DNI:', styles["Right"])
                p3_6 = Paragraph(f'{code}', styles["Left"])
                p3_7 = Paragraph(f'Grado:', styles["Right"])
                p3_8 = Paragraph(f'{grade_data}', styles["Left"])
                p3_9 = Paragraph(f'Sección:', styles["Right"])
                p3_10 = Paragraph(f'{section_data}', styles["Left"])

                # colwiths_table_3 = [_wt * 40 / 100 * 0.32, _wt * 5 / 100 * 0.32, _wt * 55 / 100 * 0.32]
                # rowwiths_table_3 = [inch * 4, inch * 0.5, inch * 0.5, inch * 0.5, inch * 0.5, inch * 0.5]
                ana_c3 = Table(
                    [(image_data,)] +
                    [(p3_2,)],
                )
                ana_c3.setStyle(TableStyle(style_table_1))

            # -------------------------------------------------------------------------------------------------- #
            # -------------------------------------------------------------------------------------------------- #
            if i + 3 < lenght_students:
                student = students[i + 3]

                first_name_data = str(student.first_name)
                last_name_data = str(student.last_name)
                code = str(student.dni)
                level_data = str(student.level.name)
                grade_data = student.grade.short_name
                section_data = student.section.name

                data = f'{first_name_data}${last_name_data}${code}${grade_data}${section_data}'

                data_encrypt = encrypt_data(data, 3)

                qr_image_bytes = generate_qrcode(data=data_encrypt)

                # Crear un archivo temporal para guardar la imagen QR
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                    tmp_file.write(qr_image_bytes)
                    tmp_file_path = tmp_file.name

                # Crear la imagen usando ReportLab Image desde el archivo temporal
                image_data = Image(tmp_file_path)

                image_data.drawHeight = inch * 4
                image_data.drawWidth = inch * 4

                p1_1 = Paragraph(f'Nombre:', styles["Right"])
                p4_2 = Paragraph(f'{first_name_data.split()[0]} {last_name_data.split()[0]}', styles["Left"])
                p1_3 = Paragraph(f'Apellido:', styles["Right"])
                p1_4 = Paragraph(f'{last_name_data}', styles["Left"])
                p1_5 = Paragraph(f'DNI:', styles["Right"])
                p1_6 = Paragraph(f'{code}', styles["Left"])
                p1_7 = Paragraph(f'Grado:', styles["Right"])
                p1_8 = Paragraph(f'{grade_data}', styles["Left"])
                p1_9 = Paragraph(f'Sección:', styles["Right"])
                p1_10 = Paragraph(f'{section_data}', styles["Left"])

                # colwiths_table_1 = [_wt * 40 / 100 * 0.32, _wt * 5 / 100 * 0.32, _wt * 55 / 100 * 0.32]
                # rowwiths_table_1 = [inch * 4, inch * 0.5, inch * 0.5, inch * 0.5, inch * 0.5, inch * 0.5]
                ana_c4 = Table(
                    [(image_data,)] +
                    [(p4_2,)],
                )
                ana_c4.setStyle(TableStyle(style_table_1))

            # -------------------------------------------------------------------------------------------------- #
            # -------------------------------------------------------------------------------------------------- #
            style_table_5 = [
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]

            colwiths_table_5 = [_wt * 23.5 / 100, _wt * 2 / 100, _wt * 23.5 / 100, _wt * 2 / 100, _wt * 23.5 / 100,
                                _wt * 2 / 100, _wt * 23.5 / 100]
            # rowwiths_table_5 = [inch * 1]
            ana_c5 = Table(
                [(ana_c1, '', ana_c2, '', ana_c3, '', ana_c4)],
                # colWidths=colwiths_table_5, rowHeights=rowwiths_table_5)
                colWidths=colwiths_table_5)
            ana_c5.setStyle(TableStyle(style_table_5))

            _dictionary.append(Spacer(width=8, height=16))
            _dictionary.append(ana_c5)

    buff = io.BytesIO()

    pz_matricial = (2.57 * inch, 11.6 * inch)
    # pz_termical = (3.14961 * inch, 11.6 * inch)
    pz_termical = (BASE * inch, ALTURA * inch)

    doc = SimpleDocTemplate(buff,
                            pagesize=pz_termical,
                            rightMargin=mr,
                            leftMargin=ml,
                            topMargin=ms,
                            bottomMargin=mi,
                            title='QRS'
                            )
    doc.build(_dictionary)
    # doc.build(elements)
    # doc.build(Story)
    #
    # response = HttpResponse(content_type='application/pdf')
    # response['Content-Disposition'] = 'attachment; filename="{}-{}.pdf"'.format(order_obj.nombres, order_obj.pagos.id)
    #

    section_name = Section.objects.get(id=section_id).short_name
    grade_name = Grade.objects.get(id=grade_id).short_name

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{grade_name} - {section_name}.pdf"'

    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow = tomorrow.replace(hour=0, minute=0, second=0)
    expires = datetime.strftime(tomorrow, "%a, %d-%b-%Y %H:%M:%S GMT")

    response.set_cookie('bp', value=1, expires=expires)

    response.write(buff.getvalue())

    buff.close()
    return response
