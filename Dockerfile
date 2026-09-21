FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Install Apify SDK
RUN pip install --no-cache-dir apify~=1.6.0

COPY . ./

# Set working directory
WORKDIR /usr/src/app

CMD ["python", "-m", "src.main"]
