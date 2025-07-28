from flask import request
from repositories.message_repository import MessageRepository
from repositories.user_repository import UserRepository
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MessageService:
    def __init__(self, socketio=None):
        self.message_repository = MessageRepository()
        self.user_repository = UserRepository()
        self.socketio = socketio
        self.active_connections = {}  # Store active user connections
        self.port = 5000  # Default port for messaging
    
    def init_socketio(self, socketio):
        """Initialize SocketIO handlers"""
        self.socketio = socketio

        @socketio.on('connect', namespace='/')
        def handle_connect():
            logger.info(f'Client connected with SID: {request.sid}')
            return {'status': 'connected', 'sid': request.sid}

        @socketio.on('disconnect', namespace='/')
        def handle_disconnect():
            logger.info(f'Client disconnected with SID: {request.sid}')
            # Remove from active connections
            for user_id, sid in list(self.active_connections.items()):
                if sid == request.sid:
                    del self.active_connections[user_id]
                    logger.info(f"Removed user {user_id} from active connections")

        @socketio.on('join', namespace='/')
        def on_join(data):
            try:
                logger.info(f'Join request received from {request.sid}: {data}')
                user_id = data.get('user_id')
                if not user_id:
                    logger.error('No user_id provided in join request')
                    return {'status': 'error', 'message': 'user_id is required'}

                # Join the user's room
                join_room(user_id)
                self.active_connections[user_id] = request.sid
                logger.info(f"User {user_id} joined room {user_id}")
                logger.info(f"Active connections: {self.active_connections}")
                
                # Get unread messages count
                unread_count = self.get_unread_count(user_id)
                
                # Send status to the specific user
                emit('status', {
                    'status': 'connected',
                    'user_id': user_id,
                    'sid': request.sid,
                    'unread_count': unread_count
                }, room=user_id)
                
                return {'status': 'joined', 'user_id': user_id, 'sid': request.sid}
            except Exception as e:
                logger.error(f'Error in join handler: {str(e)}')
                return {'status': 'error', 'message': str(e)}

        @socketio.on('leave', namespace='/')
        def on_leave(data):
            try:
                logger.info(f'Leave request received from {request.sid}: {data}')
                user_id = data.get('user_id')
                if not user_id:
                    logger.error('No user_id provided in leave request')
                    return {'status': 'error', 'message': 'user_id is required'}

                leave_room(user_id)
                if user_id in self.active_connections:
                    del self.active_connections[user_id]
                logger.info(f"User {user_id} left room")
                logger.info(f"Active connections: {self.active_connections}")
                return {'status': 'left', 'user_id': user_id}
            except Exception as e:
                logger.error(f'Error in leave handler: {str(e)}')
                return {'status': 'error', 'message': str(e)}

        @socketio.on('message', namespace='/')
        def on_message(data):
            try:
                logger.info(f'Message received from {request.sid}: {data}')
                sender_id = data.get('sender_id')
                receiver_id = data.get('receiver_id')
                message = data.get('message')

                if not all([sender_id, receiver_id, message]):
                    logger.error('Missing required fields in message')
                    return {'status': 'error', 'message': 'Missing required fields'}

                logger.info(f"Processing message from {sender_id} to {receiver_id}: {message}")
                logger.info(f"Active connections: {self.active_connections}")

                # Save message to database with unread status
                message_id = self.message_repository.save_message(sender_id, receiver_id, message, is_read=False)
                logger.info(f"Message saved to database with ID: {message_id}")

                # Prepare message response
                response = {
                    'message_id': message_id,
                    'sender_id': sender_id,
                    'receiver_id': receiver_id,
                    'message': message,
                    'is_read': False,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Send message to receiver if online
                if receiver_id in self.active_connections:
                    logger.info(f"Emitting message to room {receiver_id}")
                    emit('message', response, room=receiver_id)
                    logger.info(f"Message emitted to receiver {receiver_id}")
                else:
                    logger.info(f"Receiver {receiver_id} is not online")
                
                # Send confirmation to sender
                logger.info(f"Emitting message_sent to room {sender_id}")
                emit('message_sent', response, room=sender_id)
                logger.info(f"Confirmation sent to sender {sender_id}")
                
                return {'status': 'sent', 'message': response}
            except Exception as e:
                logger.error(f"Error handling message: {str(e)}")
                logger.error(f"Error details: {e.__class__.__name__}")
                emit('error', {'message': 'Failed to send message'}, room=request.sid)
                return {'status': 'error', 'message': str(e)}

        @socketio.on('mark_read', namespace='/')
        def on_mark_read(data):
            try:
                logger.info(f'Mark read request received from {request.sid}: {data}')
                user_id = data.get('user_id')
                message_ids = data.get('message_ids', [])
                
                if not user_id or not message_ids:
                    logger.error('Missing required fields in mark_read request')
                    return {'status': 'error', 'message': 'user_id and message_ids are required'}

                # Mark messages as read
                self.message_repository.mark_messages_as_read(message_ids, user_id)
                logger.info(f"Messages {message_ids} marked as read by user {user_id}")

                # Notify sender if online
                for message_id in message_ids:
                    message = self.message_repository.get_message(message_id)
                    if message and message['sender_id'] in self.active_connections:
                        emit('message_read', {
                            'message_id': message_id,
                            'read_by': user_id,
                            'timestamp': datetime.now().isoformat()
                        }, room=message['sender_id'])

                return {'status': 'success', 'message': 'Messages marked as read'}
            except Exception as e:
                logger.error(f"Error marking messages as read: {str(e)}")
                return {'status': 'error', 'message': str(e)}

    def get_conversations(self, user_id, page=1, limit=10):
        """Get all conversations for a user with unread counts"""
        try:
            conversations, total = self.message_repository.get_conversations(
                user_id=user_id,
                page=page,
                limit=limit
            )
            
            # Add unread count for each conversation
            for conv in conversations:
                conv['unread_count'] = self.message_repository.get_unread_count_for_conversation(
                    user_id, conv['other_user_id']
                )
            
            total_pages = (total + limit - 1) // limit
            
            return {
                'status': 'success',
                'data': {
                    'conversations': conversations,
                    'pagination': {
                        'page': page,
                        'limit': limit,
                        'total': total,
                        'total_pages': total_pages
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error getting conversations: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def get_messages(self, user_id, other_user_id, page=1, limit=20):
        """Get messages between two users"""
        try:
            messages, total = self.message_repository.get_messages_between_users(
                user_id=user_id,
                other_user_id=other_user_id,
                page=page,
                limit=limit
            )
            
            # Mark messages as read
            unread_message_ids = [msg['id'] for msg in messages if not msg['is_read'] and msg['receiver_id'] == user_id]
            if unread_message_ids:
                self.message_repository.mark_messages_as_read(unread_message_ids, user_id)
            
            total_pages = (total + limit - 1) // limit
            
            return {
                'status': 'success',
                'data': {
                    'messages': messages,
                    'pagination': {
                        'page': page,
                        'limit': limit,
                        'total': total,
                        'total_pages': total_pages
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error getting messages: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def get_unread_count(self, user_id):
        """Get total unread messages count for a user"""
        try:
            count = self.message_repository.get_unread_count(user_id)
            return count
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return 0

    def delete_message(self, message_id, user_id):
        """Delete a message (soft delete)"""
        try:
            message = self.message_repository.get_message(message_id)
            if not message:
                return {'status': 'error', 'message': 'Message not found'}
            
            if message['sender_id'] != user_id:
                return {'status': 'error', 'message': 'Not authorized to delete this message'}
            
            self.message_repository.delete_message(message_id)
            return {'status': 'success', 'message': 'Message deleted'}
        except Exception as e:
            logger.error(f"Error deleting message: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def delete_conversation(self, user_id, other_user_id):
        """Delete all messages between two users (soft delete)"""
        try:
            self.message_repository.delete_conversation(user_id, other_user_id)
            return {'status': 'success', 'message': 'Conversation deleted'}
        except Exception as e:
            logger.error(f"Error deleting conversation: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def get_conversation_messages(self, conversation_id, user_id, page=1, limit=20):
        """Get messages for a specific conversation"""
        # Check if conversation exists and user is a participant
        conversation = self.message_repository.get_conversation(conversation_id)
        
        if not conversation:
            return {
                'success': False,
                'message': 'Conversation not found'
            }
        
        if conversation['sender_id'] != user_id and conversation['recipient_id'] != user_id:
            return {
                'success': False,
                'message': 'You do not have permission to view this conversation'
            }
        
        # Get messages with pagination
        messages, total = self.message_repository.get_messages(
            conversation_id=conversation_id,
            page=page,
            limit=limit
        )
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        
        # Mark messages as read
        self.message_repository.mark_messages_as_read(conversation_id, user_id)
        
        return {
            'success': True,
            'data': {
                'conversation': conversation,
                'messages': messages,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'total_pages': total_pages
                }
            }
        }
    
    def create_conversation(self, sender_id, recipient_id, car_id, initial_message=None):
        """Create a new conversation"""
        # Check if recipient exists
        recipient = self.user_repository.get_user_by_id(recipient_id)
        
        if not recipient:
            return {
                'success': False,
                'message': 'Recipient not found'
            }
        
        # Check if sender is blocked by recipient
        if self.message_repository.is_blocked(recipient_id, sender_id):
            return {
                'success': False,
                'message': 'You cannot message this user'
            }
        
        # Check if conversation already exists
        existing_conversation = self.message_repository.get_conversation_by_participants(
            sender_id=sender_id,
            recipient_id=recipient_id,
            car_id=car_id
        )
        
        if existing_conversation:
            # If conversation exists, send initial message if provided
            if initial_message:
                self.message_repository.create_message(
                    conversation_id=existing_conversation['id'],
                    sender_id=sender_id,
                    message=initial_message
                )
            
            return {
                'success': True,
                'conversation_id': existing_conversation['id']
            }
        
        # Create new conversation
        conversation_id = self.message_repository.create_conversation(
            sender_id=sender_id,
            recipient_id=recipient_id,
            car_id=car_id
        )
        
        # Send initial message if provided
        if initial_message:
            self.message_repository.create_message(
                conversation_id=conversation_id,
                sender_id=sender_id,
                message=initial_message
            )
        
        return {
            'success': True,
            'conversation_id': conversation_id
        }
    
    def send_message(self, sender_id, receiver_id, message):
        """Send a message to a specific user"""
        try:
            logger.info(f"Attempting to send message from {sender_id} to {receiver_id}")
            
            # Validate inputs
            if not all([sender_id, receiver_id, message]):
                logger.error("Missing required fields in send_message")
                return False
                
            # Check if sender exists
            sender = self.user_repository.get_user_by_id(sender_id)
            if not sender:
                logger.error(f"Sender {sender_id} not found")
                return False
                
            # Check if receiver exists
            receiver = self.user_repository.get_user_by_id(receiver_id)
            if not receiver:
                logger.error(f"Receiver {receiver_id} not found")
                return False

            # Save message to database
            message_id = self.message_repository.save_message(sender_id, receiver_id, message, is_read=False)
            logger.info(f"Message saved to database with ID: {message_id}")

            # Prepare message response
            response = {
                'message_id': message_id,
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'message': message,
                'is_read': False,
                'timestamp': datetime.now().isoformat()
            }

            # Send message if receiver is online
            if receiver_id in self.active_connections:
                logger.info(f"Receiver {receiver_id} is online, sending message")
                self.socketio.emit('message', response, room=receiver_id)
                logger.info(f"Message sent to receiver {receiver_id}")
            else:
                logger.info(f"Receiver {receiver_id} is offline, message will be delivered when they connect")

            # Send confirmation to sender
            if sender_id in self.active_connections:
                logger.info(f"Sending confirmation to sender {sender_id}")
                self.socketio.emit('message_sent', response, room=sender_id)
                logger.info(f"Confirmation sent to sender {sender_id}")

            return True
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            logger.error(f"Error details: {e.__class__.__name__}")
            return False
    
    def mark_conversation_as_read(self, conversation_id, user_id):
        """Mark all messages in a conversation as read"""
        # Check if conversation exists and user is a participant
        conversation = self.message_repository.get_conversation(conversation_id)
        
        if not conversation:
            return {
                'success': False,
                'message': 'Conversation not found'
            }
        
        if conversation['sender_id'] != user_id and conversation['recipient_id'] != user_id:
            return {
                'success': False,
                'message': 'You do not have permission to access this conversation'
            }
        
        # Mark messages as read
        self.message_repository.mark_messages_as_read(conversation_id, user_id)
        
        return {
            'success': True
        }
    
    def get_blocked_users(self, user_id, page=1, limit=10):
        """Get all blocked users for a user"""
        # Get blocked users with pagination
        blocked_users, total = self.message_repository.get_blocked_users(
            user_id=user_id,
            page=page,
            limit=limit
        )
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        
        return {
            'blocked_users': blocked_users,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': total_pages
            }
        }

    def get_user_messages(self, user_id, other_user_id=None, limit=50):
        """Get messages for a user"""
        return self.message_repository.get_user_messages(user_id, other_user_id, limit)

    def mark_messages_as_read(self, user_id, sender_id):
        """Mark messages as read"""
        return self.message_repository.mark_messages_as_read(user_id, sender_id)
