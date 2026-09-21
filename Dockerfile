FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set working directory
WORKDIR /usr/src/app

# Install Python dependencies
RUN pip install --no-cache-dir apify~=1.6.0 playwright~=1.40.0

# Copy actor files
COPY . ./

CMD ["python", "-m", "src.main"]
