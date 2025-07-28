from services.message_service import MessageService

if __name__ == "__main__":
    print("Starting WebSocket server...")
    message_service = MessageService()
    message_service.run_server() 