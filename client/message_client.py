import socketio
import json
import sys
import time
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MessageClient:
    def __init__(self, user_id):
        self.user_id = user_id
        self.sio = socketio.Client(
            logger=True,
            engineio_logger=True,
            reconnection=True,
            reconnection_attempts=5,
            reconnection_delay=1000,
            reconnection_delay_max=5000,
            request_timeout=10
        )
        self.connected = False
        self.setup_handlers()

    def setup_handlers(self):
        @self.sio.event
        def connect():
            logger.info("Connected to server")
            self.connected = True
            # Join user's room
            self.sio.emit('join', {'user_id': self.user_id})

        @self.sio.event
        def connect_error(data):
            logger.error(f"Connection error: {data}")

        @self.sio.event
        def disconnect():
            logger.info("Disconnected from server")
            self.connected = False

        @self.sio.on('status')
        def on_status(data):
            logger.info(f"Status: {data['status']}")

        @self.sio.on('message')
        def on_message(data):
            logger.info(f"\nNew message from {data['sender_id']}: {data['message']}")

        @self.sio.on('message_sent')
        def on_message_sent(data):
            logger.info(f"Message sent successfully to {data.get('receiver_id', 'unknown')}")

        @self.sio.on('error')
        def on_error(data):
            logger.error(f"Error: {data['message']}")

    def connect(self):
        """Connect to the Socket.IO server"""
        try:
            self.sio.connect('http://localhost:5000',
                transports=['websocket', 'polling'],
                wait_timeout=10,
                namespaces=['/'],
                socketio_path='socket.io'
            )
            return True
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            return False

    def send_message(self, receiver_id, message):
        """Send a message to another user"""
        if not self.connected:
            logger.error("Not connected to server")
            return False

        try:
            self.sio.emit('message', {
                'sender_id': self.user_id,
                'receiver_id': receiver_id,
                'message': message
            })
            return True
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False

    def disconnect(self):
        """Disconnect from the server"""
        if self.connected:
            try:
                self.sio.emit('leave', {'user_id': self.user_id})
                self.sio.disconnect()
                self.connected = False
            except Exception as e:
                logger.error(f"Error disconnecting: {str(e)}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python message_client.py <user_id>")
        return

    user_id = sys.argv[1]
    client = MessageClient(user_id)
    
    if client.connect():
        print(f"Connected as user {user_id}")
        print("Commands:")
        print("  send <receiver_id> <message> - Send a message")
        print("  quit - Disconnect and exit")
        
        while client.connected:
            try:
                command = input("> ").strip()
                if command == "quit":
                    client.disconnect()
                    break
                elif command.startswith("send "):
                    parts = command.split(" ", 2)
                    if len(parts) == 3:
                        receiver_id = parts[1]
                        message = parts[2]
                        client.send_message(receiver_id, message)
                    else:
                        print("Invalid send command format")
                else:
                    print("Unknown command")
            except KeyboardInterrupt:
                client.disconnect()
                break
            except Exception as e:
                print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 