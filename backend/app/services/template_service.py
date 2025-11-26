"""Template service for generating social media post captions."""

import os
from typing import Optional

from app.schemas.post import MakerWorldData


class TemplateService:
    """Service for loading and rendering post templates."""

    def __init__(self, template_dir: str = "templates") -> None:
        """
        Initialize template service.

        Args:
            template_dir: Directory containing template files
        """
        self.template_dir = template_dir

    def load_template(self, template_name: str) -> str:
        """
        Load template from file.

        Args:
            template_name: Name of template file

        Returns:
            str: Template content

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        template_path = os.path.join(self.template_dir, template_name)

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, "r", encoding="utf-8") as file:
            return file.read()

    def render_instagram_caption(
        self,
        makerworld_data: MakerWorldData,
        custom_template: Optional[str] = None,
        full_text: Optional[str] = None,
    ) -> str:
        """
        Render Instagram caption from template.

        Args:
            makerworld_data: MakerWorld model data
            custom_template: Optional custom template string
            full_text: Optional AI-generated or custom description text

        Returns:
            str: Rendered caption
        """
        if custom_template:
            template = custom_template
        else:
            template = self.load_template("instagram_post.txt")

        # Prepare template variables
        materials_str = ", ".join(makerworld_data.materials) if makerworld_data.materials else "PLA"
        variables = {
            "title": makerworld_data.title,
            "designer_name": makerworld_data.designer_name,
            "profile_title": makerworld_data.profile_title,
            "profile_designer": makerworld_data.profile_designer,
            "print_duration": makerworld_data.print_duration,
            "material": materials_str,  # For backward compatibility
            "materials": materials_str,
            "material_amount": makerworld_data.material_amount,
            "material_lower": materials_str.lower(),
            "full_text": full_text if full_text else "",
        }

        # Render template
        rendered = template.format(**variables)

        # Clean up: Remove empty full_text placeholder lines
        if not full_text:
            # Remove lines that only contain whitespace after removing {full_text}
            lines = rendered.split("\n")
            cleaned_lines = []
            for i, line in enumerate(lines):
                # Skip empty lines that were created by removing {full_text}
                if line.strip() == "" and i > 0 and i < len(lines) - 1:
                    # Check if this is part of a double newline situation
                    if i + 1 < len(lines) and lines[i + 1].strip() == "":
                        continue
                cleaned_lines.append(line)
            rendered = "\n".join(cleaned_lines)

        return rendered

    def render_youtube_description(
        self, makerworld_data: MakerWorldData, custom_template: Optional[str] = None
    ) -> str:
        """
        Render YouTube video description.

        Args:
            makerworld_data: MakerWorld model data
            custom_template: Optional custom template string

        Returns:
            str: Rendered description
        """
        # For now, use same template as Instagram
        # Could be customized later with a separate template
        return self.render_instagram_caption(makerworld_data, custom_template)
