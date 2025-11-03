# Makefile for DemoApp Web Application

# Setup the project (creates venv and installs requirements)
setup:
	chmod +x setup.sh
	./setup.sh

# Run the web app
run:
	demoApp/venv/bin/python demoApp/manage.py runserver

# Run the web app
run_EC2:
	demoApp/venv/bin/python demoApp/manage.py runserver 0.0.0.0:8000

# Run the fake device simulator
fakedevice:
	demoApp/venv/bin/python demoApp/manage.py fake_device

# Clean up venv (remove virtual environment)
clean:
	rm -rf demoApp/venv