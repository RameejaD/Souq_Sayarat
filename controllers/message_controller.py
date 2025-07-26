from flask import request
from flask_socketio import SocketIO, join_room
from services.message_service import handle_send_message

def register_message_events(socketio: SocketIO):
    
    @socketio.on('join')
    def on_join(data):
        """
        {
            "user_id": "1"
        }
        """
        room = str(data['user_id'])
        join_room(room)
        print(f"User {data['user_id']} joined room {room}")

    @socketio.on('send_message')
    def on_send_message(data):
        """
        {
            "sender_id": 1,
            "receiver_id": 2,
            "message": "Hello"
        }
        """
        saved_message = handle_send_message(data)
        receiver_room = str(data['receiver_id'])

        # Emit message to receiver
        socketio.emit('receive_message', saved_message, room=receiver_room)
