# CSDF lab: all assignments and mini projects (pure Python, no GUI needed)
#   docker build -t csdf .
#   docker run --rm csdf                                   run every demo + self-check
#   docker run --rm -it csdf python 2_CAPTCHA/captcha.py --test
#   docker run --rm -p 2222:2222 -p 2323:2323 -p 8080:8080 csdf python 7_Honeypot/honeypot.py --public
#   docker run --rm -p 5514:5514/udp csdf python 5_LogCorrelation/log_correlator.py --listen 5514
#   docker run --rm -v "$PWD/evidence:/evidence" csdf python 8_ImageForensics/image_forensics.py /evidence/photo.jpg
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /csdf
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Run as a normal user: root ignores read-only file permissions, which would
# defeat the write-blocking demo (assignment 11) - and root containers are bad practice.
RUN useradd --create-home lab && chown -R lab /csdf
USER lab

EXPOSE 2222 2323 8080 5514/udp
CMD ["python", "run_all.py"]
