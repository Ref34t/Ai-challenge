"""
Main Streamlit app file for deployment to Streamlit Cloud
This file serves as the entry point for cloud deployment
"""

import sys
import os

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the main app
from src.frontend.app import StoryGeneratorApp

if __name__ == "__main__":
    app = StoryGeneratorApp()
    app.run()