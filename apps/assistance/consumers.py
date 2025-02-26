from channels.generic.websocket import WebsocketConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
import json

from django.db.models import Count, Q

from apps.assistance.models import GeneralAssistance
from apps.assistance.views import send_whatsapp_message_to_parent
from apps.student.models import Student
from channels.db import database_sync_to_async

class DashboardConsumer(WebsocketConsumer):
    def connect(self):
        self.slug = self.scope['url_route']['kwargs']['slug']
        self.group_name = f"dashboard_group_{self.slug}"

        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )
        # print("Conectado al grupo:", self.group_name)
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )
        # print("Desconectado del grupo:", self.group_name)

    def send_update(self, event):
        # print("Enviando datos via WebSocket:", event)
        # data = event['data']
        # self.send(text_data=json.dumps(data))

        general_assistance_id = event['general_assistance_id']

        # Hacer la consulta de asistencia cuando se actualiza
        general_assistance = GeneralAssistance.objects.get(id=general_assistance_id)
        attendance_data = general_assistance.details_general_assistance.aggregate(
            Presente=Count('state', filter=Q(state='Presente')),
            Tardanza=Count('state', filter=Q(state='Tardanza')),
            Falta=Count('state', filter=Q(state='Falta'))
        )

        self.send(text_data=json.dumps({
            "assistance": attendance_data
        }))


class FacialRecognitionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Establecer la conexión
        self.room_group_name = 'facial_recognition'

        # Unir al grupo (puedes cambiar el nombre del grupo según sea necesario)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Aceptar la conexión WebSocket
        await self.accept()

    async def disconnect(self, close_code):
        # Dejar el grupo cuando se cierre la conexión
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Recibir mensaje desde WebSocket
    async def receive(self, text_data):
        try:
            # Los datos enviados desde el cliente
            # text_data_json = json.loads(text_data)
            # print(text_data_json)

            # Procesar los datos recibidos
            # face_data = text_data_json.get('face_data', None)
            # print(face_data)
            face_data = text_data
            # Verificar si se obtuvo el dato de rostro
            if face_data:
                print("Datos de rostro recibidos:", face_data)

            # Obtener el estudiante asociado
            student_obj = await database_sync_to_async(self.get_student)()
            if student_obj:
                # print(student_obj)
                await database_sync_to_async(send_whatsapp_message_to_parent)(student_obj, "entrance")
            else:
                print("No se encontró el estudiante")

            await self.send(text_data=json.dumps({
                'message': 'Datos recibidos correctamente'
            }))
        except Exception as e:
            # Manejar errores
            print(f"Error al procesar los datos: {e}")
            await self.send(text_data=json.dumps({
                'error': 'Hubo un error al procesar los datos'
            }))

    def get_student(self):
        return Student.objects.filter(school__slug='prueba').first()
