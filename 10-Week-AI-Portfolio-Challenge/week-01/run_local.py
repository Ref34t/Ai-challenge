#!/usr/bin/env python3
"""
Local development runner for the Story Generator
Starts both the FastAPI backend and Streamlit frontend
"""

import subprocess
import time
import signal
import sys
import os
import threading
from pathlib import Path

class StoryGeneratorRunner:
    """Manages running the story generator locally."""
    
    def __init__(self):
        self.processes = []
        self.running = True
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print("\n🛑 Shutting down Story Generator...")
        self.running = False
        for process in self.processes:
            process.terminate()
        sys.exit(0)
    
    def run_fastapi(self):
        """Run the FastAPI backend."""
        print("🚀 Starting FastAPI backend on http://localhost:8000")
        try:
            process = subprocess.Popen([
                sys.executable, "-m", "uvicorn",
                "src.api.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ])
            self.processes.append(process)
            return process
        except Exception as e:
            print(f"❌ Failed to start FastAPI: {e}")
            return None
    
    def run_streamlit(self):
        """Run the Streamlit frontend."""
        print("🎨 Starting Streamlit frontend on http://localhost:8501")
        try:
            process = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run",
                "src/frontend/app.py",
                "--server.address", "0.0.0.0",
                "--server.port", "8501",
                "--server.headless", "true"
            ])
            self.processes.append(process)
            return process
        except Exception as e:
            print(f"❌ Failed to start Streamlit: {e}")
            return None
    
    def check_dependencies(self):
        """Check if required dependencies are installed."""
        required_packages = [
            "fastapi", "uvicorn", "streamlit", 
            "transformers", "torch", "requests"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print("❌ Missing required packages:")
            for package in missing_packages:
                print(f"   - {package}")
            print("\n📦 Install missing packages with:")
            print("   pip install -r requirements.txt")
            return False
        
        return True
    
    def wait_for_service(self, url, service_name, max_attempts=30):
        """Wait for a service to become available."""
        import requests
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(url, timeout=1)
                if response.status_code == 200:
                    print(f"✅ {service_name} is ready!")
                    return True
            except:
                pass
            
            time.sleep(1)
            print(f"⏳ Waiting for {service_name}... ({attempt + 1}/{max_attempts})")
        
        print(f"❌ {service_name} failed to start")
        return False
    
    def run(self):
        """Run the complete story generator application."""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("🎭 AI Story Generator - Local Development Server")
        print("=" * 50)
        
        # Check dependencies
        if not self.check_dependencies():
            return
        
        # Check if we're in the right directory
        if not os.path.exists("src/api/main.py"):
            print("❌ Please run this script from the week-01 directory")
            return
        
        try:
            # Start FastAPI backend
            api_process = self.run_fastapi()
            if not api_process:
                return
            
            # Wait for API to be ready
            if not self.wait_for_service("http://localhost:8000/health", "FastAPI API"):
                return
            
            # Start Streamlit frontend
            streamlit_process = self.run_streamlit()
            if not streamlit_process:
                return
            
            # Wait for Streamlit to be ready
            time.sleep(3)  # Streamlit takes a bit longer to start
            
            print("\n🎉 Story Generator is running!")
            print("📖 Frontend: http://localhost:8501")
            print("🔧 API Docs: http://localhost:8000/docs")
            print("💡 API Health: http://localhost:8000/health")
            print("\nPress Ctrl+C to stop the server")
            
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
                
                # Check if processes are still running
                for process in self.processes:
                    if process.poll() is not None:
                        print(f"⚠️ A process has stopped unexpectedly")
                        self.running = False
                        break
        
        except KeyboardInterrupt:
            print("\n🛑 Received shutdown signal")
        except Exception as e:
            print(f"❌ Error running story generator: {e}")
        finally:
            # Clean up processes
            for process in self.processes:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    process.kill()
            
            print("🏁 Story Generator stopped")


def main():
    """Main entry point."""
    runner = StoryGeneratorRunner()
    runner.run()


if __name__ == "__main__":
    main()