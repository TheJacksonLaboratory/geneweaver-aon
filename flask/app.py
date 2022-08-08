"""
An entrypoint to application startup
"""

from src.factory import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(port=5001)
