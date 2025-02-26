# import decimal
# import json
# import os
# from http import HTTPStatus

# import reportlab
# import io
# from datetime import datetime, timedelta, date

# from django.http import HttpResponse, JsonResponse
# from reportlab.lib.colors import Color, black, white
# from reportlab.lib.pagesizes import landscape, A5, portrait, A6, A4
# from reportlab.pdfbase import pdfmetrics
# from reportlab.pdfbase.ttfonts import TTFont
# from reportlab.platypus import SimpleDocTemplate, Paragraph, TableStyle, Spacer, Image, Flowable
# from reportlab.platypus import Table
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.graphics.shapes import Drawing
# from reportlab.graphics.barcode import qr
# from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
# from reportlab.lib import colors
# from reportlab.lib.units import cm, inch
# from reportlab.rl_settings import defaultPageSize

# from apps.school.models import Classroom
# from apps.student.models import Student
# from schoolAssistance import settings

# PAGE_HEIGHT = defaultPageSize[1]
# PAGE_WIDTH = defaultPageSize[0]

# COLOR_PDF = colors.Color(red=(152.0 / 255), green=(29.0 / 255), blue=(31.0 / 255))
# COLOR_GREEN = colors.Color(red=(27.0 / 255), green=(140.0 / 255), blue=(66.0 / 255))

# styles = getSampleStyleSheet()
# styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT, leading=30, fontName='Square', fontSize=25))
# styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, leading=8, fontName='Square', fontSize=8))
# styles.add(ParagraphStyle(name='JustifySquare', alignment=TA_JUSTIFY, leading=12, fontName='Square', fontSize=8))
# styles.add(ParagraphStyle(name='LeftSquare', alignment=TA_LEFT, leading=12, fontName='Square', fontSize=13))
# styles.add(ParagraphStyle(name='LeftSquareSmall', alignment=TA_LEFT, leading=9, fontName='Square', fontSize=10))
# styles.add(ParagraphStyle(name='LeftSquareSmall2', alignment=TA_LEFT, leading=9, fontName='Square', fontSize=8))
# styles.add(ParagraphStyle(name='Justify-Dotcirful', alignment=TA_JUSTIFY, leading=12, fontName='Dotcirful-Regular',
#                           fontSize=10))
# styles.add(
#     ParagraphStyle(name='Justify-Dotcirful-table', alignment=TA_JUSTIFY, leading=12, fontName='Dotcirful-Regular',
#                    fontSize=7))
# styles.add(ParagraphStyle(name='Justify_Bold', alignment=TA_JUSTIFY, leading=8, fontName='Square-Bold', fontSize=8))

# styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, leading=10, fontName='Square-Bold', fontSize=10,
#                           textColor=COLOR_PDF))
# styles.add(ParagraphStyle(name='Center-fecha', alignment=TA_CENTER, leading=10, fontName='Square-Bold', fontSize=10,
#                           textColor=colors.black))
# styles.add(ParagraphStyle(name='Center-datos', alignment=TA_CENTER, leading=10, fontName='Square', fontSize=10,
#                           textColor=colors.black))
# styles.add(ParagraphStyle(name='Center-arequipa', alignment=TA_CENTER, leading=19, fontName='Square-Bold', fontSize=10,
#                           textColor=COLOR_PDF))
# # styles.add(ParagraphStyle(name='Center-titulo', alignment=TA_CENTER, leading=20, fontName='Square-Bold', fontSize=20,
# #                          textColor=colors.steelblue))
# styles.add(ParagraphStyle(name='Center-titulo', alignment=TA_CENTER, leading=40, fontName='Square-Bold', fontSize=40,
#                           textColor=colors.black))
# styles.add(ParagraphStyle(name='Center-recibo', alignment=TA_CENTER, leading=20, fontName='Square-Bold', fontSize=20,
#                           textColor=colors.white))
# styles.add(ParagraphStyle(name='Center-id', alignment=TA_CENTER, leading=40, fontName='Lucida-Console', fontSize=30,
#                           textColor=colors.black))
# styles.add(ParagraphStyle(name='Center-ng', alignment=TA_CENTER, leading=10, fontName='Square-Bold', fontSize=10,
#                           textColor=colors.white))
# styles.add(
#     ParagraphStyle(name='Left', alignment=TA_LEFT, leading=30, fontName='Square', fontSize=25, textColor=colors.black))
# styles.add(
#     ParagraphStyle(name='Left-Simple', alignment=TA_LEFT, leading=15, fontName='Square', fontSize=15,
#                    textColor=colors.black))
# styles.add(ParagraphStyle(name='Left-name', alignment=TA_LEFT, leading=8, fontName='Square-Bold', fontSize=8,
#                           textColor=COLOR_PDF))
# styles.add(ParagraphStyle(name='Left-datos', alignment=TA_LEFT, leading=10, fontName='Square-Bold', fontSize=10,
#                           textColor=colors.black))

# styles.add(ParagraphStyle(name='Center4', alignment=TA_CENTER, leading=12, fontName='Square-Bold',
#                           fontSize=14, spaceBefore=6, spaceAfter=6))
# styles.add(ParagraphStyle(name='Center5', alignment=TA_LEFT, leading=15, fontName='ticketing.regular',
#                           fontSize=12))
# styles.add(
#     ParagraphStyle(name='Center-Dotcirful', alignment=TA_CENTER, leading=12, fontName='Dotcirful-Regular', fontSize=10))
# styles.add(ParagraphStyle(name='CenterTitle', alignment=TA_CENTER, leading=8, fontName='Square-Bold', fontSize=8))
# styles.add(ParagraphStyle(name='CenterTitle-Dotcirful', alignment=TA_CENTER, leading=12, fontName='Dotcirful-Regular',
#                           fontSize=10))
# styles.add(ParagraphStyle(name='CenterTitle2', alignment=TA_CENTER, leading=8, fontName='Square-Bold', fontSize=12))
# styles.add(ParagraphStyle(name='Center_Regular', alignment=TA_CENTER, leading=8, fontName='Ticketing', fontSize=10))
# styles.add(ParagraphStyle(name='Center_Bold', alignment=TA_CENTER,
#                           leading=8, fontName='Square-Bold', fontSize=12, spaceBefore=6, spaceAfter=6))
# styles.add(ParagraphStyle(name='ticketing.regular', alignment=TA_CENTER,
#                           leading=8, fontName='ticketing.regular', fontSize=14, spaceBefore=6, spaceAfter=6))
# styles.add(ParagraphStyle(name='Center2', alignment=TA_CENTER, leading=8, fontName='Ticketing', fontSize=8))
# styles.add(ParagraphStyle(name='Center3', alignment=TA_JUSTIFY, leading=8, fontName='Ticketing', fontSize=6))
# style = styles["Normal"]

# reportlab.rl_config.TTFSearchPath.append(str(settings.BASE_DIR) + '/static/fonts')
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
# # pdfmetrics.registerFont(TTFont('Romanesque_Serif', 'Romanesque Serif.ttf'))

# LOGO = "static/assets/img/logo-vet.png"

# MONTH = (
#     "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE",
#     "DICIEMBRE"
# )

# GRADE_DIC = {
#     '1': 'Primero',
#     '2': 'Segundo',
#     '3': 'Tercero',
#     '4': 'Cuarto',
#     '5': 'Quinto',
#     '6': 'Sexto'
# }

# LEVEL_DIC = {
#     'I': 'Inicial',
#     'P': 'Primaria',
#     'S': 'Secundaria'
# }


# class Background(Flowable):
#     def __init__(self, width=200, height=100, obj=None):
#         self.width = width
#         self.height = height
#         self.obj = obj

#     def wrap(self, *args):
#         """Provee el tamaño del área de dibujo"""
#         return (self.width, self.height)

#     def draw(self):
#         canvas = self.canv
#         canvas.saveState()
#         canvas.setLineWidth(1)
#         # canvas.setFillColor(black)
#         canvas.setFillColor(Color(0, 0, 0, alpha=0.4))

#         canvas.drawImage(LOGO, 200, -200, mask='auto', width=150, height=150)
#         # canvas.setStrokeGray(0.1)

#         # canvas.drawImage(firma, 195, -444, mask='auto', width=150, height=140)
#         canvas.setFont('Narrow', 12)
#         canvas.setFont('Square', 9)
#         canvas.setFillColor(white)
#         canvas.restoreState()


# def qr_code(table):
#     # generate and rescale QR
#     qr_code = qr.QrCodeWidget(table)
#     bounds = qr_code.getBounds()
#     width = bounds[2] - bounds[0]
#     height = bounds[3] - bounds[1]
#     drawing = Drawing(
#         # 3.5 * cm, 3.5 * cm, transform=[3.5 * cm / width, 0, 0, 3.5 * cm / height, 0, 0])
#         1 * cm, 1 * cm, transform=[4.5 * cm / width, 0, 0, 4.5 * cm / height, 0, 0])
#     drawing.add(qr_code)

#     return drawing


# BASE = 21
# ALTURA = 29.7


# def print_qr_pdf(request, id_student, id_classroom):
#     _wt = BASE * inch - 10 * 0.05 * inch

#     ml = 0.0 * inch
#     mr = 0.0 * inch
#     ms = 0.039 * inch
#     mi = 0.039 * inch

#     _dictionary = []
#     students = Student.objects.all()

#     filename = None

#     if id_student != 0:
#         # students = students.filter(id=int(id_student))
#         students = students.get(id=int(id_student))
#         filename = f'{students.get_fullname()}'
#     elif id_classroom != '0':
#         classroom = Classroom.objects.get(id=id_classroom)
#         students = students.filter(classroom=classroom)
#         filename = f'{classroom.grade.name} - {classroom.section.name}'

#     style_table_1 = [
#         ('BOX', (0, 0), (-1, -1), 2, colors.black),
#         ('BOX', (0, 1), (-1, -1), 2, colors.black),
#         ('SPAN', (0, 0), (-1, 0)),
#         ('ALIGN', (0, 0), (0, 0), 'LEFT'),
#         ('BOTTOMPADDING', (0, 0), (0, 0), -15),
#         ('LEFTPADDING', (0, 0), (0, 0), 60),
#         ('LEFTPADDING', (0, 1), (0, -1), 20),

#     ]

#     lenght_students = len(students)

#     ana_c1 = ''
#     ana_c2 = ''
#     ana_c3 = ''

#     if lenght_students == 1:
#         for i in range(4):
#             student = students[0]
#             data = f'{student.first_name}-{student.last_name}-{student.dni}-{student.classroom.grade.name}-{student.classroom.section.name}'
#             image_data = Image(qr_code(data))

#             image_data.drawHeight = inch * 1
#             image_data.drawWidth = inch * 1

#             p1_1 = Paragraph(f'Nombre:', styles["Right"])
#             p1_2 = Paragraph(f'{student.first_name}', styles["Left"])
#             p1_3 = Paragraph(f'Apellido:', styles["Right"])
#             p1_4 = Paragraph(f'{student.last_name}', styles["Left"])
#             p1_5 = Paragraph(f'DNI:', styles["Right"])
#             p1_6 = Paragraph(f'{student.dni}', styles["Left"])
#             p1_7 = Paragraph(f'Grado:', styles["Right"])
#             p1_8 = Paragraph(f'{student.classroom.grade.name}', styles["Left"])
#             p1_9 = Paragraph(f'Sección:', styles["Right"])
#             p1_10 = Paragraph(f'{student.classroom.section.name}', styles["Left"])

#             colwiths_table_1 = [_wt * 40 / 100 * 0.32, _wt * 5 / 100 * 0.32, _wt * 55 / 100 * 0.32]
#             rowwiths_table_1 = [inch * 4, inch * 0.5, inch * 0.5, inch * 0.5, inch * 0.5, inch * 0.5]
#             ana_c1 = Table(
#                 [(image_data, '', '')] +
#                 [(p1_1, '', p1_2)] +
#                 [(p1_3, '', p1_4)] +
#                 [(p1_5, '', p1_6)] +
#                 [(p1_7, '', p1_8)] +
#                 [(p1_9, '', p1_10)],
#                 colWidths=colwiths_table_1, rowHeights=rowwiths_table_1)
#             ana_c1.setStyle(TableStyle(style_table_1))

#             style_table_4 = [
#                 ('TOPPADDING', (0, 0), (-1, -1), 0),
#                 ('LEFTPADDING', (0, 0), (-1, -1), 0),
#                 ('RIGHPADDING', (0, 0), (-1, -1), 0),
#                 ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
#             ]

#             colwiths_table_4 = [_wt * 32 / 100, _wt * 2 / 100, _wt * 32 / 100, _wt * 2 / 100, _wt * 32 / 100]
#             # rowwiths_table_4 = [inch * 1]
#             ana_c4 = Table(
#                 [(ana_c1, '', ana_c1, '', ana_c1)],
#                 # colWidths=colwiths_table_4, rowHeights=rowwiths_table_4)
#                 colWidths=colwiths_table_4)
#             ana_c4.setStyle(TableStyle(style_table_4))

#             _dictionary.append(Spacer(width=8, height=16))
#             _dictionary.append(ana_c4)
#     else:
#         for i in range(0, lenght_students, 3):
#             if i < lenght_students:
#                 student = students[i]
#                 data = f'{student.first_name}-{student.last_name}-{student.dni}-{student.classroom.grade.name}-{student.classroom.section.name}'
#                 image_data = Image(qr_code(data))

#                 image_data.drawHeight = inch * 1
#                 image_data.drawWidth = inch * 1

#                 p1_1 = Paragraph(f'Nombre:', styles["Right"])
#                 p1_2 = Paragraph(f'{student.first_name}', styles["Left"])
#                 p1_3 = Paragraph(f'Apellido:', styles["Right"])
#                 p1_4 = Paragraph(f'{student.last_name}', styles["Left"])
#                 p1_5 = Paragraph(f'DNI:', styles["Right"])
#                 p1_6 = Paragraph(f'{student.dni}', styles["Left"])
#                 p1_7 = Paragraph(f'Grado:', styles["Right"])
#                 p1_8 = Paragraph(f'{student.classroom.grade.name}', styles["Left"])
#                 p1_9 = Paragraph(f'Sección:', styles["Right"])
#                 p1_10 = Paragraph(f'{student.classroom.section.name}', styles["Left"])

#                 colwiths_table_1 = [_wt * 40 / 100 * 0.32, _wt * 5 / 100 * 0.32, _wt * 55 / 100 * 0.32]
#                 rowwiths_table_1 = [inch * 4, inch * 0.5, inch * 0.5, inch * 0.5, inch * 0.5, inch * 0.5]
#                 ana_c1 = Table(
#                     [(image_data, '', '')] +
#                     [(p1_1, '', p1_2)] +
#                     [(p1_3, '', p1_4)] +
#                     [(p1_5, '', p1_6)] +
#                     [(p1_7, '', p1_8)] +
#                     [(p1_9, '', p1_10)],
#                     colWidths=colwiths_table_1, rowHeights=rowwiths_table_1)
#                 ana_c1.setStyle(TableStyle(style_table_1))

#             # -------------------------------------------------------------------------------------------------- #
#             # -------------------------------------------------------------------------------------------------- #
#             if i + 1 < lenght_students:
#                 student = students[i + 1]
#                 data = f'{student.first_name}-{student.last_name}-{student.dni}-{student.classroom.grade.name}-{student.classroom.section.name}'
#                 image_data = Image(qr_code(data))

#                 image_data.drawHeight = inch * 1
#                 image_data.drawWidth = inch * 1

#                 p2_1 = Paragraph(f'Nombre:', styles["Right"])
#                 p2_2 = Paragraph(f'{student.first_name}', styles["Left"])
#                 p2_3 = Paragraph(f'Apellido:', styles["Right"])
#                 p2_4 = Paragraph(f'{student.last_name}', styles["Left"])
#                 p2_5 = Paragraph(f'DNI:', styles["Right"])
#                 p2_6 = Paragraph(f'{student.dni}', styles["Left"])
#                 p2_7 = Paragraph(f'Grado:', styles["Right"])
#                 p2_8 = Paragraph(f'{student.classroom.grade.name}', styles["Left"])
#                 p2_9 = Paragraph(f'Sección:', styles["Right"])
#                 p2_10 = Paragraph(f'{student.classroom.section.name}', styles["Left"])

#                 colwiths_table_2 = [_wt * 40 / 100 * 0.32, _wt * 5 / 100 * 0.32, _wt * 55 / 100 * 0.32]
#                 rowwiths_table_2 = [inch * 4, inch * 0.5, inch * 0.5, inch * 0.5, inch * 0.5, inch * 0.5]
#                 ana_c2 = Table(
#                     [(image_data, '', '')] +
#                     [(p2_1, '', p2_2)] +
#                     [(p2_3, '', p2_4)] +
#                     [(p2_5, '', p2_6)] +
#                     [(p2_7, '', p2_8)] +
#                     [(p2_9, '', p2_10)],
#                     colWidths=colwiths_table_2, rowHeights=rowwiths_table_2)
#                 ana_c2.setStyle(TableStyle(style_table_1))

#             # -------------------------------------------------------------------------------------------------- #
#             # -------------------------------------------------------------------------------------------------- #
#             if i + 2 < lenght_students:
#                 student = students[i + 2]
#                 data = f'{student.first_name}-{student.last_name}-{student.dni}-{student.classroom.grade.name}-{student.classroom.section.name}'
#                 image_data = Image(qr_code(data))

#                 image_data.drawHeight = inch * 1
#                 image_data.drawWidth = inch * 1

#                 p3_1 = Paragraph(f'Nombre:', styles["Right"])
#                 p3_2 = Paragraph(f'{student.first_name}', styles["Left"])
#                 p3_3 = Paragraph(f'Apellido:', styles["Right"])
#                 p3_4 = Paragraph(f'{student.last_name}', styles["Left"])
#                 p3_5 = Paragraph(f'DNI:', styles["Right"])
#                 p3_6 = Paragraph(f'{student.dni}', styles["Left"])
#                 p3_7 = Paragraph(f'Grado:', styles["Right"])
#                 p3_8 = Paragraph(f'{student.classroom.grade.name}', styles["Left"])
#                 p3_9 = Paragraph(f'Sección:', styles["Right"])
#                 p3_10 = Paragraph(f'{student.classroom.section.name}', styles["Left"])

#                 colwiths_table_3 = [_wt * 40 / 100 * 0.32, _wt * 5 / 100 * 0.32, _wt * 55 / 100 * 0.32]
#                 rowwiths_table_3 = [inch * 4, inch * 0.5, inch * 0.5, inch * 0.5, inch * 0.5, inch * 0.5]
#                 ana_c3 = Table(
#                     [(image_data, '', '')] +
#                     [(p3_1, '', p3_2)] +
#                     [(p3_3, '', p3_4)] +
#                     [(p3_5, '', p3_6)] +
#                     [(p3_7, '', p3_8)] +
#                     [(p3_9, '', p3_10)],
#                     colWidths=colwiths_table_3, rowHeights=rowwiths_table_3)
#                 ana_c3.setStyle(TableStyle(style_table_1))

#             # -------------------------------------------------------------------------------------------------- #
#             # -------------------------------------------------------------------------------------------------- #

#             style_table_4 = [
#                 ('TOPPADDING', (0, 0), (-1, -1), 0),
#                 ('LEFTPADDING', (0, 0), (-1, -1), 0),
#                 ('RIGHPADDING', (0, 0), (-1, -1), 0),
#                 ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
#             ]

#             colwiths_table_4 = [_wt * 32 / 100, _wt * 2 / 100, _wt * 32 / 100, _wt * 2 / 100, _wt * 32 / 100]
#             # rowwiths_table_4 = [inch * 1]
#             ana_c4 = Table(
#                 [(ana_c1, '', ana_c2, '', ana_c3)],
#                 # colWidths=colwiths_table_4, rowHeights=rowwiths_table_4)
#                 colWidths=colwiths_table_4)
#             ana_c4.setStyle(TableStyle(style_table_4))

#             _dictionary.append(Spacer(width=8, height=16))
#             _dictionary.append(ana_c4)

#     buff = io.BytesIO()

#     pz_matricial = (2.57 * inch, 11.6 * inch)
#     # pz_termical = (3.14961 * inch, 11.6 * inch)
#     pz_termical = (BASE * inch, ALTURA * inch)

#     doc = SimpleDocTemplate(buff,
#                             pagesize=pz_termical,
#                             rightMargin=mr,
#                             leftMargin=ml,
#                             topMargin=ms,
#                             bottomMargin=mi,
#                             title=f'{classroom.grade.name} - {classroom.section.name}'
#                             )
#     doc.build(_dictionary)
#     # doc.build(elements)
#     # doc.build(Story)
#     #
#     # response = HttpResponse(content_type='application/pdf')
#     # response['Content-Disposition'] = 'attachment; filename="{}-{}.pdf"'.format(order_obj.nombres, order_obj.pagos.id)
#     #

#     response = HttpResponse(content_type='application/pdf')

#     # response['Content-Disposition'] = 'attachment; filename="{}.pdf"'.format(f'{classroom.grade.name} - {classroom.section.name}')
#     response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'

#     tomorrow = datetime.now() + timedelta(days=1)
#     tomorrow = tomorrow.replace(hour=0, minute=0, second=0)
#     expires = datetime.strftime(tomorrow, "%a, %d-%b-%Y %H:%M:%S GMT")

#     response.set_cookie('bp', value=1, expires=expires)

#     response.write(buff.getvalue())

#     buff.close()
#     return response
