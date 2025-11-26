"""AI text generation service using Groq API."""

from typing import Optional

import httpx

from app.config import settings


class AITextServiceError(Exception):
    """Custom exception for AI text service errors."""

    pass


class AITextService:
    """Service for generating text using Groq AI API."""

    def __init__(self):
        """Initialize AI text service."""
        self.api_key = settings.groq_api_key
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"  # Updated: Fast and high-quality model

    async def generate_product_description(
        self,
        keywords: str,
        product_title: str,
        designer_name: Optional[str] = None,
        print_duration: Optional[str] = None,
        materials: Optional[list] = None,
    ) -> str:
        """
        Generate a product description based on keywords and product details.

        Args:
            keywords: User-provided keywords/theme for the description
            product_title: Title of the 3D print
            designer_name: Name of the designer
            print_duration: How long the print took
            materials: List of materials used

        Returns:
            str: Generated description text

        Raises:
            AITextServiceError: If text generation fails
        """
        if not self.api_key:
            raise AITextServiceError("Groq API key not configured")

        # Build context from product details
        context_parts = [f"Product: {product_title}"]
        if designer_name:
            context_parts.append(f"Designer: {designer_name}")
        if print_duration:
            context_parts.append(f"Print time: {print_duration}")
        if materials:
            context_parts.append(f"Materials: {', '.join(materials)}")

        context = " | ".join(context_parts)

        # Create prompt for AI
        prompt = f"""Write a short, engaging Instagram caption (2-3 sentences, max 280 characters) for a 3D printed item.

Product details: {context}

Keywords/Theme: {keywords}

Write in English. Be enthusiastic and highlight what makes this print special. Focus on the aesthetics, use case, or unique features mentioned in the keywords. Don't use hashtags."""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a creative social media content writer specializing in 3D printing and maker content. Write concise, engaging descriptions.",
                            },
                            {
                                "role": "user",
                                "content": prompt,
                            },
                        ],
                        "temperature": 0.8,
                        "max_tokens": 150,
                    },
                )

                if response.status_code != 200:
                    error_detail = response.text
                    raise AITextServiceError(
                        f"Groq API error (status {response.status_code}): {error_detail}"
                    )

                data = response.json()
                generated_text = data["choices"][0]["message"]["content"].strip()

                return generated_text

        except httpx.TimeoutException:
            raise AITextServiceError("Groq API request timed out")
        except httpx.RequestError as e:
            raise AITextServiceError(f"Groq API request failed: {str(e)}")
        except (KeyError, IndexError) as e:
            raise AITextServiceError(f"Invalid Groq API response format: {str(e)}")
        except Exception as e:
            raise AITextServiceError(f"Unexpected error: {str(e)}")
