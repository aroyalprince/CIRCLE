# social/consumers.py
import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework.authtoken.models import Token

waiting_users = []  # simple queue

class VideoCallConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # Authenticate via token in query string
        token_key = self.scope['query_string'].decode().split('token=')[-1]
        user = await self.get_user(token_key)
        if not user:
            await self.close(code=4001)
            return

        self.user = user
        self.room_group = None
        await self.accept()
        print(f"[WS] {user.username} connected")

    async def disconnect(self, close_code):
        # Remove from waiting queue if still there
        global waiting_users
        waiting_users = [u for u in waiting_users if u['socket'] != self]

        # Notify partner if in a room
        if self.room_group:
            await self.channel_layer.group_send(self.room_group, {
                'type': 'peer_left',
                'username': self.user.username
            })
            await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type')

        if msg_type == 'find_match':
            await self.find_match()

        elif msg_type == 'offer':
            await self.channel_layer.group_send(self.room_group, {
                'type': 'webrtc_offer',
                'offer': data['offer'],
                'sender': self.channel_name
            })

        elif msg_type == 'answer':
            await self.channel_layer.group_send(self.room_group, {
                'type': 'webrtc_answer',
                'answer': data['answer'],
                'sender': self.channel_name
            })

        elif msg_type == 'ice_candidate':
            await self.channel_layer.group_send(self.room_group, {
                'type': 'webrtc_ice',
                'candidate': data['candidate'],
                'sender': self.channel_name
            })

        elif msg_type == 'next':
            await self.leave_room()
            await self.find_match()

    async def find_match(self):
        global waiting_users

        # Remove self from queue first (avoid double queue)
        waiting_users = [u for u in waiting_users if u['socket'] != self]

        # Find a waiting partner
        partner = None
        for u in waiting_users:
            if u['username'] != self.user.username:
                partner = u
                break

        if partner:
            waiting_users.remove(partner)
            room_id = f"room_{uuid.uuid4().hex[:10]}"

            # Join both into the group
            self.room_group = room_id
            partner['socket'].room_group = room_id

            await self.channel_layer.group_add(room_id, self.channel_name)
            await self.channel_layer.group_add(room_id, partner['socket'].channel_name)

            # Tell the CALLER (self) to create the offer
            await self.send(text_data=json.dumps({
                'type': 'match_found',
                'room_id': room_id,
                'role': 'caller'   # YOU send the offer
            }))

            # Tell the partner to wait for offer
            await partner['socket'].send(text_data=json.dumps({
                'type': 'match_found',
                'room_id': room_id,
                'role': 'receiver'  # YOU wait for offer
            }))
        else:
            # Nobody waiting — add self to queue
            waiting_users.append({
                'socket': self,
                'username': self.user.username
            })
            await self.send(text_data=json.dumps({'type': 'waiting'}))

    async def leave_room(self):
        if self.room_group:
            await self.channel_layer.group_send(self.room_group, {
                'type': 'peer_left',
                'username': self.user.username
            })
            await self.channel_layer.group_discard(self.room_group, self.channel_name)
            self.room_group = None

    # ---- Channel layer event handlers ----
    async def webrtc_offer(self, event):
        if event['sender'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'offer',
                'offer': event['offer']
            }))

    async def webrtc_answer(self, event):
        if event['sender'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'answer',
                'answer': event['answer']
            }))

    async def webrtc_ice(self, event):
        if event['sender'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'ice_candidate',
                'candidate': event['candidate']
            }))

    async def peer_left(self, event):
        await self.send(text_data=json.dumps({'type': 'peer_left'}))

    @database_sync_to_async
    def get_user(self, token_key):
        try:
            return Token.objects.get(key=token_key).user
        except Token.DoesNotExist:
            return None