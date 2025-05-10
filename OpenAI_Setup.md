# OpenAI Setup for Invoice Manager

This document provides a comprehensive guide on how OpenAI is integrated into the Invoice Manager project. It covers everything you need to know to understand the existing implementation and how to adapt it for your own projects.

## Table of Contents

1. [Introduction](#introduction)
2. [Installation Requirements](#installation-requirements)
3. [Configuration](#configuration)
4. [API Key Management](#api-key-management)
5. [Core Integration](#core-integration)
6. [Prompt Engineering](#prompt-engineering)
7. [Error Handling and Resilience](#error-handling-and-resilience)
8. [Testing OpenAI Integration](#testing-openai-integration)
9. [Logging and Monitoring](#logging-and-monitoring)
10. [Best Practices](#best-practices)

## Introduction

The Invoice Manager uses OpenAI's GPT-4o model to refine and enhance invoice data extraction. After initial OCR and basic field extraction, the OpenAI model analyzes the extracted text and improves the structured data by leveraging its language understanding capabilities.

## Installation Requirements

To use OpenAI in your project, install the required packages:

```bash
pip install openai python-dotenv
```

The project uses the latest OpenAI Python client (v1.x+) which supports the new API structure.

## Configuration

OpenAI settings are configured in the main `config.yaml` file:

```yaml
# LLM extraction
openai:
  model: gpt-4o
  temperature: 0
  max_tokens: 2000
  few_shot_examples: 3
  log_prompts: true
```

### Configuration Parameters

- **model**: The OpenAI model to use (e.g., `gpt-4o`)
- **temperature**: Controls randomness (0 for deterministic responses)
- **max_tokens**: Maximum tokens for the model response
- **few_shot_examples**: Number of examples to include in prompts
- **log_prompts**: Whether to log prompts for debugging

## API Key Management

The project uses environment variables for API key management:

```python
# From src/extraction/openai_refiner.py
# Ensure OpenAI API key is set
if "OPENAI_API_KEY" not in os.environ:
    logger.warning("OPENAI_API_KEY environment variable not set")

# Initialize OpenAI client
self.client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
```

### Setting Up API Keys

1. Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your-openai-api-key
   ```

2. Load environment variables in your code:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

3. For CI/CD pipelines, set secrets in GitHub Actions:
   ```yaml
   # From .github/workflows/ci.yml
   env:
     OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
   ```

## Core Integration

The main integration is handled by the `OpenAIRefiner` class in `src/extraction/openai_refiner.py`. Here's how it works:

### Initialization

```python
def __init__(self, config: Dict):
    """Initialize the OpenAI refiner."""
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
    
    # Initialize OpenAI client
    self.client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    logger.info(f"Initialized OpenAI refiner with model: {self.model}")
```

### Main Refinement Function

```python
def refine(self, ocr_text: str, initial_fields: Dict) -> Dict:
    """Refine extracted fields using OpenAI."""
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
    
    logger.info(f"OpenAI refinement complete, extracted {len(refined_fields) - 1} fields")
    return refined_fields
```

### API Call Handling

```python
def _call_openai(self, messages: List[Dict]) -> Dict:
    """Call OpenAI API for invoice field refinement."""
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
```

## Prompt Engineering

The project uses Jinja2 templates for OpenAI prompts, located in `src/extraction/prompts/`:

### Template Structure

The `invoice_extraction.j2` template includes:
- System instructions
- Schema definition
- Extraction instructions
- Few-shot examples
- Output format requirements

```python
def _create_prompt(self, ocr_text: str, initial_fields: Dict, schema: Dict) -> List[Dict]:
    """Create a prompt for OpenAI to refine extracted fields."""
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
```

### Few-Shot Examples

Examples are stored in `src/extraction/prompts/examples.json`:

```python
def _get_few_shot_examples(self) -> List[Dict]:
    """Get few-shot examples for the prompt."""
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
```

## Error Handling and Resilience

The implementation includes several error handling mechanisms:

1. **API Key Validation**:
   ```python
   if "OPENAI_API_KEY" not in os.environ:
       logger.warning("OPENAI_API_KEY environment variable not set")
   ```

2. **API Call Error Handling**:
   ```python
   try:
       response = self.client.chat.completions.create(...)
   except Exception as e:
       logger.error(f"Error calling OpenAI API: {str(e)}")
       return {}
   ```

3. **Response Parsing Error Handling**:
   ```python
   try:
       result = json.loads(content)
       return result
   except json.JSONDecodeError as e:
       logger.error(f"Error parsing OpenAI response: {str(e)}")
       return {}
   ```

## Testing OpenAI Integration

The project includes tests to verify OpenAI integration in `test_api_keys.py`:

```python
def test_openai_api_key():
    """Test if OpenAI API key is valid by making a simple chat completion call."""
    print("\n--- Testing OpenAI API Key ---")
    
    try:
        from openai import OpenAI
        
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            print("❌ OPENAI_API_KEY environment variable not found.")
            return False
            
        print(f"✓ Found OPENAI_API_KEY: {openai_api_key[:5]}{'*' * (len(openai_api_key) - 5)}")
        
        # Initialize OpenAI client with context manager
        try:
            with OpenAI(api_key=openai_api_key) as client:
                # Make a simple chat completion request
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": "Say 'API connection successful'"}],
                    max_tokens=10
                )
                
                content = response.choices[0].message.content
                print(f"✓ Successfully connected to OpenAI API")
                print(f"✓ Response: {content}")
                return True
        except Exception as e:
            print(f"❌ Failed to use OpenAI API: {str(e)}")
            return False
            
    except ImportError:
        print("❌ 'openai' package not installed or outdated. Install the latest version with 'pip install --upgrade openai'")
        return False
```

## Logging and Monitoring

### Prompt Logging

If enabled in configuration (`log_prompts: true`), all prompts are logged to `docs/prompt_log.md`:

```python
def _log_prompt(self, messages: List[Dict], initial_fields: Dict) -> None:
    """Log prompt and response for auditing and improvement."""
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
```

### Latency Monitoring

The project includes special logging for OpenAI API latency in the logging configuration:

```python
# From src/utils/logger.py
def _add_openai_latency_handler(logger: logging.Logger, log_dir: Path) -> None:
    """Add special handler for OpenAI API latency metrics."""
    # Create file handler for OpenAI latency logs
    latency_handler = logging.FileHandler(
        log_dir / "openai_latency.log",
        mode="a"
    )
    latency_handler.setLevel(logging.INFO)
    latency_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        "%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(latency_handler)
```

## Best Practices

Based on the project implementation, here are some best practices for OpenAI integration:

1. **Environment Variables**: Keep API keys in environment variables, never hardcode them.

2. **Comprehensive Error Handling**: Handle API errors and parsing failures gracefully.

3. **Structured Prompts**: Use template systems like Jinja2 for maintainable, consistent prompts.

4. **Few-Shot Learning**: Include relevant examples to guide the model's responses.

5. **Schema-Based Responses**: Define a clear schema for the model output format.

6. **JSON Response Format**: Use OpenAI's `response_format={"type": "json_object"}` for structured outputs.

7. **Logging and Monitoring**: Keep logs of prompts and responses for debugging and improvement.

8. **Testing**: Implement tests to verify API connectivity and response handling.

9. **Configuration Management**: Keep OpenAI-specific settings in configuration files.

10. **Context Managers**: Use context managers for API clients when appropriate.

By following these guidelines, you can implement a robust OpenAI integration similar to what's used in the Invoice Manager project. 