# Makefile for DemoApp Web Application

# Setup the project (creates venv and installs requirements)
setup:
	chmod +x setup.sh && ./setup.sh

# Activate the virtual environment (Mac/WSL)
activate:
	source demoApp/venv/bin/activate

# Run the web app
run:
	source demoApp/venv/bin/activate && python demoApp/manage.py runserver

# Clean up venv (remove virtual environment)
clean:
	rm -rf demoApp/venv
