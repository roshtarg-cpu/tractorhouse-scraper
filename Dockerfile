FROM apify/actor-python:3.11

# Install Playwright and Chromium
RUN pip install --no-cache-dir playwright==1.40.0

# Install Chromium browser
RUN playwright install chromium

# Install system dependencies for Chromium
RUN playwright install-deps chromium

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

CMD ["python", "-m", "src.main"]
