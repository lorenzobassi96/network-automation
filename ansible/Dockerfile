# Ansible Execution Environment for the NETCONF network automation playbook.
#
# Build:
#   podman build -t netconf-ee .
# Run (see README for full examples):
#   podman run --rm --network host netconf-ee --tags=show

FROM python:3.11-slim

# System packages needed to build the Python NETCONF/XML dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libxml2-dev \
        libxslt1-dev \
        openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Ansible core + runner (runner makes this a valid execution environment)
RUN pip install --no-cache-dir ansible-core>=2.16 ansible-runner

WORKDIR /ansible

# Install Python and Ansible collection dependencies first for better layer caching
COPY requirements.txt requirements.yml ./
RUN pip install --no-cache-dir -r requirements.txt \
    && ansible-galaxy collection install -r requirements.yml

# Copy the playbook project
COPY . .

ENV ANSIBLE_HOST_KEY_CHECKING=False

ENTRYPOINT ["ansible-playbook", "-i", "inventory.yml", "network_automation.yml"]
CMD ["--tags=show"]
