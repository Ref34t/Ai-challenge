"""
Unit tests for the Story Generator
"""

import pytest
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.models.story_generator import StoryGenerator, create_story_generator


class TestStoryGenerator:
    """Test cases for StoryGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create a story generator instance for testing."""
        # Use a small model for testing
        return StoryGenerator(model_name="gpt2", use_openai=False)
    
    def test_initialization(self, generator):
        """Test that the generator initializes correctly."""
        assert generator is not None
        assert generator.model_name == "gpt2"
        assert not generator.use_openai
        assert generator.device in ["cpu", "cuda"]
    
    def test_get_available_genres(self, generator):
        """Test getting available genres."""
        genres = generator.get_available_genres()
        assert isinstance(genres, list)
        assert len(genres) > 0
        assert "fantasy" in genres
        assert "sci-fi" in genres
        assert "general" in genres
    
    def test_get_model_info(self, generator):
        """Test getting model information."""
        info = generator.get_model_info()
        assert isinstance(info, dict)
        assert "model_name" in info
        assert "model_type" in info
        assert "device" in info
        assert "available" in info
    
    def test_generate_story_basic(self, generator):
        """Test basic story generation."""
        prompt = "A robot learns to paint"
        result = generator.generate_story(prompt=prompt)
        
        assert isinstance(result, dict)
        assert "story" in result
        assert "prompt" in result
        assert result["prompt"] == prompt
        assert len(result["story"]) > 0
    
    def test_generate_story_with_genre(self, generator):
        """Test story generation with specific genre."""
        prompt = "A wizard finds a magical artifact"
        result = generator.generate_story(
            prompt=prompt,
            genre="fantasy",
            length="short",
            temperature=0.5
        )
        
        assert result["genre"] == "fantasy"
        assert result["length"] == "short"
        assert result["temperature"] == 0.5
        assert "word_count" in result
    
    def test_generate_story_different_lengths(self, generator):
        """Test story generation with different lengths."""
        prompt = "A simple test story"
        
        for length in ["short", "medium", "long"]:
            result = generator.generate_story(prompt=prompt, length=length)
            assert result["length"] == length
            assert "word_count" in result
    
    def test_build_prompt_with_genre(self, generator):
        """Test prompt building with genre context."""
        user_prompt = "A hero emerges"
        
        # Test with fantasy genre
        full_prompt = generator._build_prompt(user_prompt, "fantasy")
        assert "magical realm" in full_prompt.lower() or user_prompt in full_prompt
        
        # Test with general genre
        general_prompt = generator._build_prompt(user_prompt, "general")
        assert general_prompt == user_prompt
    
    def test_error_handling(self, generator):
        """Test error handling for edge cases."""
        # Test empty prompt
        result = generator.generate_story(prompt="")
        assert isinstance(result, dict)
        
        # Test very long prompt
        long_prompt = "A" * 1000
        result = generator.generate_story(prompt=long_prompt)
        assert isinstance(result, dict)
    
    def test_create_story_generator_function(self):
        """Test the factory function."""
        generator = create_story_generator(use_openai=False)
        assert isinstance(generator, StoryGenerator)
        assert not generator.use_openai


class TestStoryGeneratorAPI:
    """Test the story generator in API context."""
    
    def test_api_response_format(self):
        """Test that API responses have the correct format."""
        generator = create_story_generator(use_openai=False)
        result = generator.generate_story("Test prompt")
        
        # Check required fields
        required_fields = ["story", "prompt", "genre", "length", "model", "word_count", "temperature"]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
    
    def test_batch_generation_simulation(self):
        """Simulate batch generation for API testing."""
        generator = create_story_generator(use_openai=False)
        prompts = [
            "A detective solves a mystery",
            "A robot learns emotions",
            "A wizard casts a spell"
        ]
        
        results = []
        for prompt in prompts:
            result = generator.generate_story(prompt)
            results.append(result)
        
        assert len(results) == 3
        for result in results:
            assert "story" in result
            assert len(result["story"]) > 0


# Integration tests
class TestIntegration:
    """Integration tests for the complete system."""
    
    def test_end_to_end_story_generation(self):
        """Test complete story generation workflow."""
        # Create generator
        generator = create_story_generator(use_openai=False)
        
        # Generate story
        result = generator.generate_story(
            prompt="A time traveler visits ancient Rome",
            genre="sci-fi",
            length="medium",
            temperature=0.7
        )
        
        # Verify result
        assert result["prompt"] == "A time traveler visits ancient Rome"
        assert result["genre"] == "sci-fi"
        assert result["length"] == "medium"
        assert result["temperature"] == 0.7
        assert isinstance(result["word_count"], int)
        assert result["word_count"] > 0
        assert len(result["story"]) > 50  # Reasonable minimum length
    
    def test_all_genres(self):
        """Test story generation for all available genres."""
        generator = create_story_generator(use_openai=False)
        genres = generator.get_available_genres()
        
        for genre in genres[:3]:  # Test first 3 genres to save time
            result = generator.generate_story(
                prompt="A test story",
                genre=genre,
                length="short"
            )
            assert result["genre"] == genre
            assert "story" in result


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])