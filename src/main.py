"""Main entry point for the AI-Powered Technician Workflow System."""

import asyncio
import signal
import sys
from core.websocket import WebSocketClient
from core.audio import AudioHandler
from core.tools import Tools
from utils.logging import setup_logger

logger = setup_logger(__name__)

class Application:
    def __init__(self):
        self.websocket = WebSocketClient()
        self.audio = AudioHandler()
        self.tools = Tools()
        self.running = False

    async def startup(self):
        """Initialize application components."""
        try:
            # Connect to WebSocket
            if not await self.websocket.connect():
                raise Exception("Failed to connect to WebSocket server")

            # Initialize audio
            if not self.audio.start_recording():
                raise Exception("Failed to initialize audio")

            self.running = True
            logger.info("Application started successfully")
            return True
        except Exception as e:
            logger.error(f"Startup failed: {e}")
            return False

    async def shutdown(self):
        """Clean up application resources."""
        self.running = False
        await self.websocket.disconnect()
        self.audio.cleanup()
        logger.info("Application shut down successfully")

    async def run(self):
        """Main application loop."""
        if not await self.startup():
            return

        try:
            while self.running:
                # Main application logic will go here
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            await self.shutdown()

def signal_handler(sig, frame):
    """Handle system signals."""
    logger.info("Shutting down...")
    sys.exit(0)

async def main():
    """Application entry point."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    app = Application()
    await app.run()

if __name__ == "__main__":
    asyncio.run(main()) 