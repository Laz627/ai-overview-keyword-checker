# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file into the image
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and the necessary browsers
RUN apt-get update && apt-get install -y wget \
    && wget https://github.com/microsoft/playwright-python/releases/download/v1.14.1/playwright-python-1.14.1.tar.gz \
    && pip install playwright-python-1.14.1.tar.gz \
    && playwright install

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "script.py"]
