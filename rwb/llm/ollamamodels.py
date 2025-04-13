import ollama


def list_models():
    """List available models using the Ollama API."""
    try:
        models = ollama.list()['models']
        return [model['model'] for model in models]
    except Exception as e:
        print(f"Error listing models: {str(e)}")
        return []