import os
import sys
import threading
import time
import webview
from django.core.management import execute_from_command_line

def start_django_server():
    """Starts the Django server in the background."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xjhs_pis.settings')
    
    # --noreload is critical. If you don't use this, the .exe will crash later.
    execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:8000', '--noreload'])

if __name__ == '__main__':
    # 1. Start Django in a background thread
    server_thread = threading.Thread(target=start_django_server)
    server_thread.daemon = True
    server_thread.start()

    # 2. Wait exactly 1.5 seconds for Django to boot up
    time.sleep(1.5)

    # 3. Create the Windows Desktop Application window
    webview.create_window(
        title='XJHS-PIS: Prefect Information System',
        url='http://127.0.0.1:8000/',
        width=1280,
        height=720,
        resizable=True,
        maximized=True # Starts full screen for that classic app feel
    )
    
    # 4. Launch the window
    webview.start()