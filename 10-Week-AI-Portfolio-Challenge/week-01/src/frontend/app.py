"""
Streamlit Frontend for AI Story Generator
Beautiful, user-friendly interface for story generation
"""

import streamlit as st
import requests
import json
import os
from typing import Dict, Any
import time
from datetime import datetime
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch

# Page configuration
st.set_page_config(
    page_title="AI Story Generator",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .story-container {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .metadata-container {
        background-color: #e9ecef;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .genre-badge {
        background-color: #1f77b4;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin: 0.25rem;
        display: inline-block;
    }
    .stButton > button {
        background-color: #1f77b4;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #0056b3;
    }
</style>
""", unsafe_allow_html=True)


class StoryGeneratorApp:
    """Main Streamlit application for story generation."""
    
    def __init__(self):
        self.api_base_url = "http://localhost:8000"  # Local FastAPI server
        self.genres_info = {}
        self.model_info = {}
        
        # Initialize session state
        if 'generated_stories' not in st.session_state:
            st.session_state.generated_stories = []
        if 'api_available' not in st.session_state:
            st.session_state.api_available = False
    
    def check_api_availability(self):
        """Check if the FastAPI backend is available."""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            if response.status_code == 200:
                st.session_state.api_available = True
                return True
        except:
            pass
        
        st.session_state.api_available = False
        return False
    
    def load_genres(self):
        """Load available genres from the API."""
        try:
            response = requests.get(f"{self.api_base_url}/genres")
            if response.status_code == 200:
                genres_data = response.json()
                self.genres_info = {genre['name']: genre for genre in genres_data}
                return list(self.genres_info.keys())
        except:
            pass
        
        # Fallback genres if API is not available
        return ["general", "fantasy", "sci-fi", "mystery", "romance", "horror", "adventure", "thriller", "comedy"]
    
    def load_model_info(self):
        """Load model information from the API."""
        try:
            response = requests.get(f"{self.api_base_url}/model-info")
            if response.status_code == 200:
                self.model_info = response.json()
        except:
            self.model_info = {"model_name": "Unknown", "model_type": "Unknown"}
    
    def generate_story_api(self, prompt: str, genre: str, length: str, temperature: float) -> Dict[str, Any]:
        """Generate story using the FastAPI backend."""
        try:
            payload = {
                "prompt": prompt,
                "genre": genre,
                "length": length,
                "temperature": temperature
            }
            
            response = requests.post(
                f"{self.api_base_url}/generate",
                json=payload,
                timeout=60  # Generous timeout for story generation
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"API Error: {response.status_code}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timed out. Please try again."}
        except Exception as e:
            return {"success": False, "error": f"Connection error: {str(e)}"}
    
    def generate_story_fallback(self, prompt: str, genre: str, length: str, temperature: float) -> Dict[str, Any]:
        """Fallback story generation when API is not available."""
        # Simple template-based story generation for demo purposes
        genre_templates = {
            "fantasy": f"In a mystical realm, {prompt.lower()}. Magic filled the air as our hero embarked on an extraordinary quest that would change their destiny forever.",
            "sci-fi": f"In the distant future, {prompt.lower()}. Advanced technology and alien worlds awaited as humanity faced its greatest challenge yet.",
            "mystery": f"The detective pondered the case: {prompt.lower()}. Clues were scattered like breadcrumbs, leading to a truth more shocking than anyone imagined.",
            "romance": f"Love was in the air when {prompt.lower()}. Two hearts were about to discover that sometimes the most unexpected encounters lead to the most beautiful stories.",
            "horror": f"Darkness crept in as {prompt.lower()}. What started as an ordinary day would soon become a nightmare that would haunt them forever.",
        }
        
        template = genre_templates.get(genre, f"{prompt}. This story unfolds with unexpected twists and turns, revealing characters who must overcome challenges and discover truths about themselves and their world.")
        
        # Extend based on length
        length_multipliers = {"short": 1, "medium": 2, "long": 3}
        multiplier = length_multipliers.get(length, 2)
        
        extended_story = template
        for i in range(multiplier - 1):
            extended_story += " As the story continues, new revelations emerge and the plot thickens with each passing moment."
        
        return {
            "story": extended_story,
            "prompt": prompt,
            "genre": genre,
            "length": length,
            "model": "Fallback Template",
            "word_count": len(extended_story.split()),
            "temperature": temperature,
            "success": True
        }
    
    def export_story_to_pdf(self, story_data: Dict[str, Any]) -> io.BytesIO:
        """Export story to PDF format."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title = Paragraph(f"AI Generated Story - {story_data['genre'].title()}", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Metadata
        metadata = f"""
        <b>Prompt:</b> {story_data['prompt']}<br/>
        <b>Genre:</b> {story_data['genre'].title()}<br/>
        <b>Length:</b> {story_data['length'].title()}<br/>
        <b>Model:</b> {story_data.get('model', 'Unknown')}<br/>
        <b>Word Count:</b> {story_data.get('word_count', 'Unknown')}<br/>
        <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        story.append(Paragraph(metadata, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Story content
        story_content = story_data['story'].replace('\n', '<br/>')
        story.append(Paragraph(story_content, styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def render_sidebar(self):
        """Render the sidebar with controls and information."""
        st.sidebar.markdown("# 📖 Story Generator")
        
        # API Status
        if st.session_state.api_available:
            st.sidebar.success("✅ API Connected")
            if self.model_info:
                st.sidebar.info(f"Model: {self.model_info.get('model_name', 'Unknown')}")
        else:
            st.sidebar.warning("⚠️ API Offline (Using Fallback)")
        
        # OpenAI Configuration
        st.sidebar.markdown("### 🔑 OpenAI Configuration")
        openai_key = st.sidebar.text_input(
            "OpenAI API Key (Optional)", 
            type="password",
            help="Add your OpenAI API key for enhanced story generation"
        )
        
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key
            st.sidebar.success("OpenAI key configured!")
        
        # Story History
        st.sidebar.markdown("### 📚 Story History")
        if st.session_state.generated_stories:
            for i, story in enumerate(reversed(st.session_state.generated_stories[-5:])):
                with st.sidebar.expander(f"Story {len(st.session_state.generated_stories) - i}"):
                    st.write(f"**Genre:** {story['genre']}")
                    st.write(f"**Prompt:** {story['prompt'][:50]}...")
                    st.write(f"**Words:** {story.get('word_count', 'Unknown')}")
        else:
            st.sidebar.info("No stories generated yet")
        
        # Clear History
        if st.sidebar.button("🗑️ Clear History"):
            st.session_state.generated_stories = []
            st.experimental_rerun()
    
    def render_main_interface(self):
        """Render the main story generation interface."""
        # Header
        st.markdown('<h1 class="main-header">🎭 AI Story Generator</h1>', unsafe_allow_html=True)
        st.markdown("Generate creative stories with AI! Choose your genre, set your preferences, and let the magic happen.")
        
        # Check API availability
        api_available = self.check_api_availability()
        
        # Load data
        available_genres = self.load_genres()
        if api_available:
            self.load_model_info()
        
        # Story generation form
        with st.form("story_generation_form"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                prompt = st.text_area(
                    "✍️ Story Prompt",
                    placeholder="Enter your story idea, beginning, or theme...",
                    height=100,
                    help="Describe what you want your story to be about. Be as creative as you like!"
                )
            
            with col2:
                genre = st.selectbox(
                    "🎭 Genre",
                    available_genres,
                    help="Choose the genre for your story"
                )
                
                length = st.selectbox(
                    "📏 Length",
                    ["short", "medium", "long"],
                    index=1,
                    help="Select how long you want your story to be"
                )
                
                temperature = st.slider(
                    "🌡️ Creativity",
                    min_value=0.1,
                    max_value=1.0,
                    value=0.7,
                    step=0.1,
                    help="Higher values make the story more creative and unpredictable"
                )
            
            # Generate button
            submitted = st.form_submit_button("🚀 Generate Story", use_container_width=True)
        
        # Process story generation
        if submitted and prompt:
            if len(prompt.strip()) < 10:
                st.error("Please provide a more detailed prompt (at least 10 characters)")
                return
            
            with st.spinner("🎨 Crafting your story... This may take a moment"):
                if api_available:
                    result = self.generate_story_api(prompt, genre, length, temperature)
                else:
                    result = self.generate_story_fallback(prompt, genre, length, temperature)
                
                if result.get("success", True):
                    # Add to session state
                    st.session_state.generated_stories.append(result)
                    
                    # Display the story
                    self.display_story(result)
                else:
                    st.error(f"Failed to generate story: {result.get('error', 'Unknown error')}")
        
        elif submitted:
            st.error("Please enter a story prompt!")
    
    def display_story(self, story_data: Dict[str, Any]):
        """Display the generated story with formatting and export options."""
        st.markdown("---")
        st.markdown("## 📖 Your Generated Story")
        
        # Story metadata
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="genre-badge">{story_data["genre"].title()}</div>', unsafe_allow_html=True)
        with col2:
            st.metric("Words", story_data.get("word_count", "Unknown"))
        with col3:
            st.metric("Length", story_data["length"].title())
        with col4:
            st.metric("Model", story_data.get("model", "Unknown"))
        
        # Story content
        st.markdown(f'<div class="story-container">{story_data["story"]}</div>', unsafe_allow_html=True)
        
        # Export options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 Copy to Clipboard"):
                st.code(story_data["story"])
        
        with col2:
            # PDF Export
            pdf_buffer = self.export_story_to_pdf(story_data)
            st.download_button(
                label="📄 Download PDF",
                data=pdf_buffer,
                file_name=f"story_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )
        
        with col3:
            # Text Export
            st.download_button(
                label="📝 Download TXT",
                data=story_data["story"],
                file_name=f"story_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        
        # Rating and feedback
        st.markdown("### 💭 How was your story?")
        rating = st.select_slider(
            "Rate this story:",
            options=["😞 Poor", "😐 Fair", "😊 Good", "😍 Excellent", "🤩 Amazing"],
            value="😊 Good"
        )
        
        feedback = st.text_input("Any feedback or suggestions?", placeholder="Optional feedback...")
        
        if st.button("📤 Submit Feedback"):
            st.success("Thank you for your feedback! It helps improve the story generator.")
    
    def run(self):
        """Run the Streamlit application."""
        self.render_sidebar()
        self.render_main_interface()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666; margin-top: 2rem;'>
            <p>🤖 AI Story Generator | Built with Streamlit & Hugging Face Transformers</p>
            <p>Part of the 10-Week AI Portfolio Challenge</p>
        </div>
        """, unsafe_allow_html=True)


# Run the application
if __name__ == "__main__":
    app = StoryGeneratorApp()
    app.run()