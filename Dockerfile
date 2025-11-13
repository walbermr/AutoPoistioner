# Pull base image.
FROM ubuntu:22.04

# Install.
RUN \
  sed -i 's/# \(.*multiverse$\)/\1/g' /etc/apt/sources.list && \
  apt-get -y update && \ 
  apt-get -y upgrade && \
  apt-get update && \
  apt-get install -yq tzdata && \
  ln -fs /usr/share/zoneinfo/America/New_York /etc/localtime && \
  dpkg-reconfigure -f noninteractive tzdata && \
  apt-get install -y git build-essential software-properties-common bison flex libpng-dev zlib1g-dev && \
  apt-get install -y byobu curl git htop man unzip vim wget gcc make automake libtool && \
  apt-get install -y libboost-all-dev cmake && \
  apt-get install -y python3 && \
  rm -rf /var/lib/apt/lists/*

ENV PATH="/root/miniconda3/bin:${PATH}"
ARG PATH="/root/miniconda3/bin:${PATH}"

RUN arch=$(uname -m) && \
  if [ "$arch" = "x86_64" ]; then \
  MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"; \
  elif [ "$arch" = "aarch64" ]; then \
  MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh"; \
  else \
  echo "Unsupported architecture: $arch"; \
  exit 1; \
  fi && \
  wget $MINICONDA_URL -O miniconda.sh && \
  mkdir -p /root/.conda && \
  bash miniconda.sh -b -p /root/miniconda3 && \
  rm -f miniconda.sh

RUN conda --version

COPY ./env.yaml /root/env.yaml

RUN conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main \
 && conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

RUN conda env create -f /root/env.yaml

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

RUN echo "source activate bio-gen-lean" > ~/.bashrc

ENV PATH /opt/conda/envs/bio-gen-lean/bin:$PATH
ENV CONDA_DEFAULT_ENV bio-gen-lean

CMD ["bash"]