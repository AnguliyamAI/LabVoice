How to make Dockerfile?

1) base image
2) pip install requirments.txt
3) pytorch cuda install(pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121)
4) download espeak(https://github.com/espeak-ng/espeak-ng/releases/download/1.51/espeak-ng-1.51.tar.gz)
5) set env variables (PHONEMIZER_ESPEAK_PATH: c:\Program Files\eSpeak NG,
PHONEMIZER_ESPEAK_LIBRARY: c:\Program Files\eSpeak NG\libespeak-ng.dll)
6) python app.py



Basic docker file
```bash

# 1. Base image with CUDA 12.1
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu20.04
# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt install -y python3-pip

# Copy the requirements file and install dependencies in the virtual environment
COPY . .

RUN pip3 install -r requirements.txt -v
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
# 3. Install PyTorch with CUDA 12.1 support

# 4. Download and install eSpeak-NG
RUN wget https://github.com/espeak-ng/espeak-ng/releases/download/1.51/espeak-ng-1.51.tar.gz && \
    tar -xvzf espeak-ng-1.51.tar.gz && \
    cd espeak-ng-1.51 && \
    ./configure && make && make install && \
    cd .. && rm -rf espeak-ng-1.51 espeak-ng-1.51.tar.gz

# 5. Set environment variables for eSpeak-NG
ENV PHONEMIZER_ESPEAK_PATH="/usr/local/share/espeak-ng-data"
ENV PHONEMIZER_ESPEAK_LIBRARY="/usr/local/lib/libespeak-ng.so"

# 7. Run the application using the virtual environment's Python
CMD ["python", "app.py"]

```
