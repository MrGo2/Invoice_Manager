"""
OpenAI Refiner

This module refines extracted invoice fields using OpenAI's GPT-4o model.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

import openai
from jinja2 import Environment, FileSystemLoader

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class OpenAIRefiner:
    """Refines extracted invoice fields using OpenAI."""
    
    def __init__(self, config: Dict):
        """
        Initialize the OpenAI refiner.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.model = config["openai"]["model"]
        self.temperature = config["openai"]["temperature"]
        self.max_tokens = config["openai"]["max_tokens"]
        self.few_shot_examples = config["openai"]["few_shot_examples"]
        self.log_prompts = config["openai"]["log_prompts"]
        self.last_timestamp = None
        
        # Set up Jinja2 for prompt templates
        templates_dir = Path(__file__).parent / "prompts"
        self.jinja_env = Environment(loader=FileSystemLoader(templates_dir))
        
        # Ensure OpenAI API key is set
        if "OPENAI_API_KEY" not in os.environ:
            logger.warning("OPENAI_API_KEY environment variable not set")
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        logger.info(f"Initialized OpenAI refiner with model: {self.model}")
    
    def refine(self, ocr_text: str, initial_fields: Dict) -> Dict:
        """
        Refine extracted fields using OpenAI.
        
        Args:
            ocr_text: Raw OCR text from the invoice
            initial_fields: Dictionary of initially extracted fields
            
        Returns:
            Refined dictionary of invoice fields
        """
        logger.info("Refining extracted fields with OpenAI")
        
        # Get invoice schema
        schema_path = Path(self.config["validation"]["schema"])
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        # Create prompt
        prompt = self._create_prompt(ocr_text, initial_fields, schema)
        
        # Log prompt if enabled
        if self.log_prompts:
            self._log_prompt(prompt, initial_fields)
        
        # Call OpenAI API
        refined_fields = self._call_openai(prompt)
        
        # Record timestamp
        self.last_timestamp = datetime.now().isoformat()
        
        # Add metadata
        if "metadata" not in refined_fields:
            refined_fields["metadata"] = {}
        
        refined_fields["metadata"].update({
            "extraction_method": "openai",
            "extraction_model": self.model,
            "extraction_timestamp": self.last_timestamp
        })
        
        # Preserve previous metadata if available
        if "metadata" in initial_fields:
            for key, value in initial_fields["metadata"].items():
                if key not in refined_fields["metadata"]:
                    refined_fields["metadata"][key] = value
        
        logger.info(f"OpenAI refinement complete, extracted {len(refined_fields) - 1} fields")  # -1 for metadata
        return refined_fields
    
    def _create_prompt(self, ocr_text: str, initial_fields: Dict, schema: Dict) -> List[Dict]:
        """
        Create a prompt for OpenAI to refine extracted fields.
        
        Args:
            ocr_text: Raw OCR text
            initial_fields: Initially extracted fields
            schema: JSON schema for invoice data
            
        Returns:
            List of message dictionaries for OpenAI API
        """
        # Load template
        template = self.jinja_env.get_template("invoice_extraction.j2")
        
        # Simplify schema for prompt
        simplified_schema = self._simplify_schema(schema)
        
        # Prepare few-shot examples
        examples = self._get_few_shot_examples()
        
        # Render system message
        system_message = template.render(
            schema=simplified_schema,
            examples=examples
        )
        
        # Create messages for OpenAI
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"OCR Text:\n\n{ocr_text}\n\nInitial fields extracted:\n\n{json.dumps(initial_fields, indent=2, ensure_ascii=False)}"}
        ]
        
        return messages
    
    def _call_openai(self, messages: List[Dict]) -> Dict:
        """
        Call OpenAI API for invoice field refinement.
        
        Args:
            messages: List of message dictionaries for the API
            
        Returns:
            Refined dictionary of invoice fields
        """
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing OpenAI response: {str(e)}")
                logger.error(f"Response content: {content}")
                return {}
                
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            # Return initial fields in case of error
            return {}
    
    def _simplify_schema(self, schema: Dict) -> Dict:
        """
        Simplify JSON schema for use in prompts.
        
        Args:
            schema: Full JSON schema
            
        Returns:
            Simplified schema for prompts
        """
        simplified = {
            "type": "object",
            "properties": {}
        }
        
        # Add required fields
        if "required" in schema:
            simplified["required"] = schema["required"]
        
        # Simplify properties
        for prop_name, prop_details in schema.get("properties", {}).items():
            simplified["properties"][prop_name] = {
                "type": prop_details.get("type", "string"),
                "description": prop_details.get("description", "")
            }
            
            # Add pattern if available
            if "pattern" in prop_details:
                simplified["properties"][prop_name]["pattern"] = prop_details["pattern"]
            
            # Add enum if available
            if "enum" in prop_details:
                simplified["properties"][prop_name]["enum"] = prop_details["enum"]
                
            # Handle nested objects (line_items)
            if prop_name == "line_items" and "items" in prop_details:
                simplified["properties"][prop_name]["items"] = {
                    "type": "object",
                    "properties": {}
                }
                
                for item_prop, item_details in prop_details.get("items", {}).get("properties", {}).items():
                    simplified["properties"][prop_name]["items"]["properties"][item_prop] = {
                        "type": item_details.get("type", "string"),
                        "description": item_details.get("description", "")
                    }
        
        return simplified
    
    def _get_few_shot_examples(self) -> List[Dict]:
        """
        Get few-shot examples for the prompt.
        
        Returns:
            List of example dictionaries
        """
        # Load examples from JSON file
        examples_path = Path(__file__).parent / "prompts" / "examples.json"
        
        if examples_path.exists():
            try:
                with open(examples_path, 'r', encoding='utf-8') as f:
                    all_examples = json.load(f)
                
                # Return the requested number of examples
                return all_examples[:self.few_shot_examples]
            except Exception as e:
                logger.error(f"Error loading few-shot examples: {str(e)}")
        
        # Return empty list if examples file not found or error loading
        return []
    
    def _log_prompt(self, messages: List[Dict], initial_fields: Dict) -> None:
        """
        Log prompt and response for auditing and improvement.
        
        Args:
            messages: Messages sent to OpenAI
            initial_fields: Initial extracted fields
        """
        try:
            prompt_log_path = Path("docs/prompt_log.md")
            
            # Create parent directory if it doesn't exist
            prompt_log_path.parent.mkdir(exist_ok=True)
            
            # Format the log entry
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"""
## Prompt Log Entry - {timestamp}

### System Message
```
{messages[0]['content']}
```

### User Message
```
{messages[1]['content']}
```

### Initial Fields
```json
{json.dumps(initial_fields, indent=2, ensure_ascii=False)}
```

---

"""
            
            # Append to log file
            with open(prompt_log_path, 'a+', encoding='utf-8') as f:
                f.write(log_entry)
                
        except Exception as e:
            logger.error(f"Error logging prompt: {str(e)}") 