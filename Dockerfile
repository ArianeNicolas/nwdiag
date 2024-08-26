FROM python:3.9
RUN apt-get update ; apt-get install -y  fonts-ipafont ; apt-get clean

# Copy the requirements file to the temp directory
COPY requirements.txt /tmp/
# Install the Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt
#VOLUME ["/app"]
WORKDIR /app
# Copy the entire project to the working directory
COPY . .
# Build and install the Python package
RUN python setup.py install
# Set the entrypoint to a shell for testing
CMD ["bash"]
#CMD ["nwdiag","--help"]