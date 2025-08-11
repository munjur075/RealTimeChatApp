import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from ChatApp.models import Room, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = f"room_{self.scope['url_route']['kwargs']['room_name']}"
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        # data contains keys: message, sender, room_name

        event = {
            'type': 'send_message',
            'message': data,
        }

        await self.channel_layer.group_send(self.room_name, event)

    async def send_message(self, event):
        data = event['message']
        await self.create_message(data)

        # Send flat JSON (no nested 'message' key)
        await self.send(text_data=json.dumps({
            'sender': data['sender'],
            'message': data['message']
        }))

    @database_sync_to_async
    def create_message(self, data):
        try:
            room = Room.objects.get(room_name=data['room_name'])
        except Room.DoesNotExist:
            # Optionally create room or just return
            return
        # Save message
        Message.objects.create(room=room, sender=data['sender'], message=data['message'])
