"""
Story Generator Model using FREE Hugging Face transformers
Supports both free models and optional OpenAI integration
"""

import os
import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    pipeline,
    set_seed
)
from typing import Dict, List, Optional
import logging

# Optional OpenAI import (only if API key provided)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StoryGenerator:
    """
    AI Story Generator using free Hugging Face models with optional OpenAI support.
    """
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium", use_openai: bool = False):
        """
        Initialize the story generator.
        
        Args:
            model_name: Hugging Face model name (default: free Microsoft DialoGPT)
            use_openai: Whether to use OpenAI API (requires API key)
        """
        self.model_name = model_name
        self.use_openai = use_openai
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Genre-specific prompt templates
        self.genre_prompts = {
            "fantasy": "In a magical realm where dragons soar through crystal skies",
            "sci-fi": "In the year 2157, aboard the starship Odyssey",
            "mystery": "The detective arrived at the scene just as the fog began to lift",
            "romance": "Their eyes met across the crowded café on a rainy Tuesday morning",
            "horror": "The old house at the end of Maple Street had been empty for decades",
            "adventure": "The treasure map was torn and faded, but the X was still visible",
            "thriller": "The phone rang at exactly midnight, just as they had warned",
            "comedy": "It was supposed to be a simple trip to the grocery store"
        }
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the appropriate model based on configuration."""
        if self.use_openai and OPENAI_AVAILABLE:
            self._initialize_openai()
        else:
            self._initialize_huggingface()
    
    def _initialize_openai(self):
        """Initialize OpenAI API if key is provided."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OpenAI API key not found. Falling back to Hugging Face.")
            self.use_openai = False
            self._initialize_huggingface()
            return
        
        openai.api_key = api_key
        logger.info("OpenAI API initialized successfully")
    
    def _initialize_huggingface(self):
        """Initialize free Hugging Face model."""
        try:
            logger.info(f"Loading Hugging Face model: {self.model_name}")
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None
            )
            
            # Add padding token if it doesn't exist
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Create text generation pipeline
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            
            logger.info("Hugging Face model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            # Fallback to a smaller, more reliable model
            self._fallback_to_gpt2()
    
    def _fallback_to_gpt2(self):
        """Fallback to GPT-2 if other models fail."""
        logger.info("Falling back to GPT-2 model")
        self.model_name = "gpt2"
        
        self.tokenizer = AutoTokenizer.from_pretrained("gpt2")
        self.model = AutoModelForCausalLM.from_pretrained("gpt2")
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.generator = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            device=-1  # CPU only for fallback
        )
    
    def generate_story(
        self,
        prompt: str,
        genre: str = "general",
        length: str = "medium",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, str]:
        """
        Generate a story based on the given prompt and parameters.
        
        Args:
            prompt: User's story prompt
            genre: Story genre (fantasy, sci-fi, mystery, etc.)
            length: Story length (short, medium, long)
            temperature: Creativity level (0.1-1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary containing the generated story and metadata
        """
        # Set random seed for reproducibility
        set_seed(42)
        
        # Build full prompt with genre context
        full_prompt = self._build_prompt(prompt, genre)
        
        # Determine story length
        if max_tokens is None:
            length_mapping = {
                "short": 150,
                "medium": 300,
                "long": 500
            }
            max_tokens = length_mapping.get(length, 300)
        
        try:
            if self.use_openai and OPENAI_AVAILABLE:
                story = self._generate_with_openai(full_prompt, max_tokens, temperature)
            else:
                story = self._generate_with_huggingface(full_prompt, max_tokens, temperature)
            
            return {
                "story": story,
                "prompt": prompt,
                "genre": genre,
                "length": length,
                "model": "OpenAI GPT" if self.use_openai else self.model_name,
                "word_count": len(story.split()),
                "temperature": temperature
            }
            
        except Exception as e:
            logger.error(f"Error generating story: {e}")
            return {
                "story": "Sorry, I encountered an error while generating your story. Please try again with a different prompt.",
                "error": str(e),
                "prompt": prompt,
                "genre": genre
            }
    
    def _build_prompt(self, user_prompt: str, genre: str) -> str:
        """Build the full prompt with genre context."""
        genre_intro = self.genre_prompts.get(genre, "")
        
        if genre_intro and genre != "general":
            return f"{genre_intro}. {user_prompt}"
        else:
            return user_prompt
    
    def _generate_with_openai(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate story using OpenAI API."""
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            return response.choices[0].text.strip()
        
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            # Fallback to Hugging Face if OpenAI fails
            return self._generate_with_huggingface(prompt, max_tokens, temperature)
    
    def _generate_with_huggingface(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate story using Hugging Face model."""
        try:
            # Generate text
            outputs = self.generator(
                prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                top_k=50,
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.eos_token_id,
                num_return_sequences=1
            )
            
            # Extract generated text (remove original prompt)
            generated_text = outputs[0]['generated_text']
            story = generated_text[len(prompt):].strip()
            
            return story
            
        except Exception as e:
            logger.error(f"Hugging Face generation error: {e}")
            return "I apologize, but I'm having trouble generating a story right now. Please try again."
    
    def get_available_genres(self) -> List[str]:
        """Get list of available story genres."""
        return list(self.genre_prompts.keys()) + ["general"]
    
    def get_model_info(self) -> Dict[str, str]:
        """Get information about the current model."""
        return {
            "model_name": self.model_name,
            "model_type": "OpenAI" if self.use_openai else "Hugging Face",
            "device": self.device,
            "available": True
        }


def create_story_generator(use_openai: bool = False) -> StoryGenerator:
    """
    Factory function to create a story generator instance.
    
    Args:
        use_openai: Whether to use OpenAI API (requires OPENAI_API_KEY env var)
        
    Returns:
        Configured StoryGenerator instance
    """
    # Check if OpenAI API key is available
    if use_openai and not os.getenv("OPENAI_API_KEY"):
        logger.warning("OpenAI API key not found. Using free Hugging Face model.")
        use_openai = False
    
    # Choose the best free model based on available resources
    if torch.cuda.is_available():
        # Use a more capable model if GPU is available
        model_name = "microsoft/DialoGPT-large"
    else:
        # Use smaller model for CPU
        model_name = "microsoft/DialoGPT-medium"
    
    return StoryGenerator(model_name=model_name, use_openai=use_openai)


if __name__ == "__main__":
    # Test the story generator
    generator = create_story_generator()
    
    test_prompt = "A young wizard discovers a mysterious book in the library"
    result = generator.generate_story(
        prompt=test_prompt,
        genre="fantasy",
        length="medium",
        temperature=0.8
    )
    
    print("Generated Story:")
    print("=" * 50)
    print(result["story"])
    print("\nMetadata:")
    print(f"Genre: {result['genre']}")
    print(f"Word Count: {result['word_count']}")
    print(f"Model: {result['model']}")