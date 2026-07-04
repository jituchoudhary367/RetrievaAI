import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
from sentence_transformers import SentenceTransformer

try:
    print("Trying default...")
    model = SentenceTransformer('BAAI/bge-small-en-v1.5', device='cpu')
    print("Success 1!")
except Exception as e:
    print(f"Failed 1: {e}")

try:
    print("Trying low_cpu_mem_usage=False...")
    model = SentenceTransformer('BAAI/bge-small-en-v1.5', device='cpu', model_kwargs={'low_cpu_mem_usage': False})
    print("Success 2!")
except Exception as e:
    print(f"Failed 2: {e}")

try:
    print("Trying device_map=cpu...")
    model = SentenceTransformer('BAAI/bge-small-en-v1.5', device='cpu', model_kwargs={'device_map': 'cpu'})
    print("Success 3!")
except Exception as e:
    print(f"Failed 3: {e}")

try:
    print("Trying weights_only=False...")
    model = SentenceTransformer('BAAI/bge-small-en-v1.5', device='cpu', model_kwargs={'torch_dtype': 'auto', 'low_cpu_mem_usage': False})
    print("Success 4!")
except Exception as e:
    print(f"Failed 4: {e}")

