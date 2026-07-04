import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app

def print_routes():
    for route in app.routes:
        if hasattr(route, "methods"):
            print(f"{list(route.methods)} {route.path}")
        else:
            print(f"MOUNT {route.path}")

if __name__ == "__main__":
    print_routes()
