import json
from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework.exceptions import AuthenticationFailed
import jwt
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from asgiref.sync import sync_to_async
from usersapp.models import User
import time
import redis

redis_instance = redis.Redis(**settings.REDIS_CONFIG)

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.username1 = self.scope['url_route']['kwargs']['username1']
        self.username2 = self.scope['url_route']['kwargs']['username2']
        print("Pookie bear")

        # Ensure enrollment numbers are in a consistent order (sorted)
        sorted_username_numbers = sorted([self.username1, self.username2])

        # Create the room name by joining the sorted enrollment numbers
        self.room_name = f"{sorted_username_numbers[0]}_{sorted_username_numbers[1]}"
        self.room_group_name = f'chat_{self.room_name}'

        print(f"Connecting to room: {self.room_group_name}")

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print(f"Connected to room: {self.room_group_name}")

    async def disconnect(self, close_code):
        print(f"Disconnecting from room: {self.room_group_name}, Close code: {close_code}")
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data['message']
            room = self.room_name
            username = self.username1

            # Print received data for debugging purposes
            print(f"Received data: {data}")
            print(f"Received message: {message} from user: {username} in room: {room}")

            # Save the message to the database
            await self.save_message(username, room, message)

            # Prepare the data to be sent to the group
            group_data = {
                'type': 'chat_message',
                'message': message,
                'user': username,
            }

            # Print what is being sent to the group for debugging purposes
            print(f"Sending to group: {group_data}")

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                group_data
            )
        except Exception as e:
            print(f"Error receiving message: {str(e)}")


    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        user= event['user']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'user': user
        }))
        print(f"Sent message: {message} to WebSocket for user: {user}")

    # Handle message deletion event
    async def delete_messages_event(self, event):
        # Notify WebSocket clients that all messages have been deleted
        await self.send(text_data=json.dumps({
            'action': 'delete_messages',
            'message': 'All messages in the room have been deleted'
        }))
        print(f"Notified users about message deletion in room: {self.room_group_name}")

    @sync_to_async
    def save_message(self, username, room, content):
        try:
            # Check if user exists, catch User.DoesNotExist
            user = User.objects.get(username=username)
            
            # Store message in Redis
            message = {
                'user': user.username,  # Use username or another identifying field
                'content': content,
                'timestamp': time.time()
            }
            redis_instance.lpush(room, json.dumps(message))

            return JsonResponse({'message': 'Message stored successfully'})
        
        except User.DoesNotExist:
            print(f"User does not exist: {username}")
            return HttpResponseBadRequest('User does not exist!')
        
        except json.JSONDecodeError:
            return HttpResponseBadRequest('Invalid JSON format')
        
        except Exception as e:
            print(f"Error saving message: {str(e)}")
            return HttpResponseBadRequest('Error saving message')
