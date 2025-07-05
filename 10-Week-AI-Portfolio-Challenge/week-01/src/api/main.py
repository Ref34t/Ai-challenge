"""
FastAPI backend for the Story Generator
Provides REST API endpoints for story generation
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import logging
import os
from contextlib import asynccontextmanager

from src.models.story_generator import create_story_generator, StoryGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
story_generator: Optional[StoryGenerator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown events."""
    # Startup
    global story_generator
    logger.info("Starting Story Generator API...")
    
    # Initialize story generator
    use_openai = bool(os.getenv("OPENAI_API_KEY"))
    story_generator = create_story_generator(use_openai=use_openai)
    logger.info(f"Story generator initialized with model: {story_generator.model_name}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Story Generator API...")


# Initialize FastAPI app
app = FastAPI(
    title="AI Story Generator API",
    description="Generate creative stories using AI with customizable genres and styles",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class StoryRequest(BaseModel):
    """Request model for story generation."""
    prompt: str = Field(..., min_length=1, max_length=500, description="Story prompt or beginning")
    genre: str = Field(default="general", description="Story genre")
    length: str = Field(default="medium", regex="^(short|medium|long)$", description="Story length")
    temperature: float = Field(default=0.7, ge=0.1, le=1.0, description="Creativity level (0.1-1.0)")
    max_tokens: Optional[int] = Field(default=None, ge=50, le=1000, description="Maximum tokens to generate")

    class Config:
        schema_extra = {
            "example": {
                "prompt": "A young detective discovers a hidden room in an old mansion",
                "genre": "mystery",
                "length": "medium",
                "temperature": 0.8,
                "max_tokens": 300
            }
        }


class StoryResponse(BaseModel):
    """Response model for generated stories."""
    story: str
    prompt: str
    genre: str
    length: str
    model: str
    word_count: int
    temperature: float
    success: bool = True
    error: Optional[str] = None


class GenreInfo(BaseModel):
    """Information about available genres."""
    name: str
    description: str
    example_prompt: str


class ModelInfo(BaseModel):
    """Information about the current model."""
    model_name: str
    model_type: str
    device: str
    available: bool


# API Routes

@app.get("/", tags=["General"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to the AI Story Generator API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["General"])
async def health_check():
    """Health check endpoint."""
    global story_generator
    
    if story_generator is None:
        raise HTTPException(status_code=503, detail="Story generator not initialized")
    
    model_info = story_generator.get_model_info()
    return {
        "status": "healthy",
        "model_available": model_info["available"],
        "model_name": model_info["model_name"]
    }


@app.post("/generate", response_model=StoryResponse, tags=["Story Generation"])
async def generate_story(request: StoryRequest):
    """
    Generate a story based on the provided prompt and parameters.
    
    - **prompt**: The story prompt or beginning (required)
    - **genre**: Story genre (optional, default: general)
    - **length**: Story length - short, medium, or long (optional, default: medium)
    - **temperature**: Creativity level from 0.1 to 1.0 (optional, default: 0.7)
    - **max_tokens**: Maximum tokens to generate (optional)
    """
    global story_generator
    
    if story_generator is None:
        raise HTTPException(status_code=503, detail="Story generator not initialized")
    
    try:
        # Generate story
        result = story_generator.generate_story(
            prompt=request.prompt,
            genre=request.genre,
            length=request.length,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Check if generation was successful
        if "error" in result:
            return StoryResponse(
                story="",
                prompt=request.prompt,
                genre=request.genre,
                length=request.length,
                model=story_generator.model_name,
                word_count=0,
                temperature=request.temperature,
                success=False,
                error=result["error"]
            )
        
        return StoryResponse(**result)
        
    except Exception as e:
        logger.error(f"Error generating story: {e}")
        raise HTTPException(status_code=500, detail=f"Story generation failed: {str(e)}")


@app.get("/genres", response_model=List[GenreInfo], tags=["Story Generation"])
async def get_genres():
    """Get available story genres with descriptions and examples."""
    global story_generator
    
    if story_generator is None:
        raise HTTPException(status_code=503, detail="Story generator not initialized")
    
    genre_descriptions = {
        "general": {
            "description": "General fiction without specific genre constraints",
            "example": "Write about an unexpected encounter at a coffee shop"
        },
        "fantasy": {
            "description": "Magical worlds with dragons, wizards, and mythical creatures",
            "example": "A young mage discovers an ancient spellbook"
        },
        "sci-fi": {
            "description": "Science fiction with futuristic technology and space exploration",
            "example": "The first human colony on Mars faces an unknown threat"
        },
        "mystery": {
            "description": "Detective stories and puzzles to solve",
            "example": "A valuable painting disappears from a locked room"
        },
        "romance": {
            "description": "Love stories and relationships",
            "example": "Two rivals are forced to work together on a project"
        },
        "horror": {
            "description": "Scary and suspenseful stories",
            "example": "Strange sounds come from the basement every night"
        },
        "adventure": {
            "description": "Action-packed journeys and expeditions",
            "example": "Treasure hunters discover a map to a lost civilization"
        },
        "thriller": {
            "description": "High-stakes suspense and tension",
            "example": "A witness to a crime goes into hiding"
        },
        "comedy": {
            "description": "Humorous and light-hearted stories",
            "example": "Everything goes wrong on the most important day"
        }
    }
    
    available_genres = story_generator.get_available_genres()
    
    return [
        GenreInfo(
            name=genre,
            description=genre_descriptions.get(genre, {}).get("description", ""),
            example_prompt=genre_descriptions.get(genre, {}).get("example", "")
        )
        for genre in available_genres
    ]


@app.get("/model-info", response_model=ModelInfo, tags=["General"])
async def get_model_info():
    """Get information about the current story generation model."""
    global story_generator
    
    if story_generator is None:
        raise HTTPException(status_code=503, detail="Story generator not initialized")
    
    info = story_generator.get_model_info()
    return ModelInfo(**info)


@app.post("/generate-batch", response_model=List[StoryResponse], tags=["Story Generation"])
async def generate_batch_stories(requests: List[StoryRequest]):
    """
    Generate multiple stories in batch.
    Useful for generating variations or multiple stories at once.
    Limited to 5 requests per batch to prevent overload.
    """
    global story_generator
    
    if story_generator is None:
        raise HTTPException(status_code=503, detail="Story generator not initialized")
    
    if len(requests) > 5:
        raise HTTPException(status_code=400, detail="Batch size limited to 5 requests")
    
    results = []
    for request in requests:
        try:
            result = story_generator.generate_story(
                prompt=request.prompt,
                genre=request.genre,
                length=request.length,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            if "error" in result:
                results.append(StoryResponse(
                    story="",
                    prompt=request.prompt,
                    genre=request.genre,
                    length=request.length,
                    model=story_generator.model_name,
                    word_count=0,
                    temperature=request.temperature,
                    success=False,
                    error=result["error"]
                ))
            else:
                results.append(StoryResponse(**result))
                
        except Exception as e:
            logger.error(f"Error in batch generation: {e}")
            results.append(StoryResponse(
                story="",
                prompt=request.prompt,
                genre=request.genre,
                length=request.length,
                model=story_generator.model_name if story_generator else "unknown",
                word_count=0,
                temperature=request.temperature,
                success=False,
                error=str(e)
            ))
    
    return results


# Custom exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": "2024-01-01T00:00:00Z"  # You can add proper timestamp
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run the API server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )