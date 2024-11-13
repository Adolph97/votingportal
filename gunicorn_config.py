import os

# Bind to 0.0.0.0 to allow external access
bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
keepalive = 120
timeout = 120 