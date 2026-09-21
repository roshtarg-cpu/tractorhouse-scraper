FROM apify/actor-python-playwright-chrome:3.11

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install chromium \
    && playwright install-deps chromium

COPY . ./

CMD ["python", "-m", "src.main"]
