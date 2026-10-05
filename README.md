# StreamFetch: Event-Driven Asset Processing Pipeline
![Python](https://img.shields.io/badge/python-3.14-3776AB.svg?style=flat&logo=python&logoColor=white)
![aiohttp](https://img.shields.io/badge/aiohttp-3.14-%233776AB.svg?style=flat&logo=python&logoColor=white)
![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=flat&logo=kubernetes&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)
![AWS S3](https://img.shields.io/badge/AWS_S3-569A31?style=flat&logo=amazons3&logoColor=white)
![AWS Lambda](https://img.shields.io/badge/AWS_Lambda-FF9900?style=flat&logo=awslambda&logoColor=white)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=flat&logo=redis&logoColor=white)
![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=flat&logo=nginx&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-yellow.svg?style=flat)

An asynchronous microservice for high-speed media downloading and event-driven processing within the AWS cloud infrastructure. This project demonstrates Cloud-Native principles, container orchestration, and Serverless architecture.


## System Architecture

1. **Ingress & API (Kubernetes):** The Nginx Ingress Controller routes external HTTP traffic to the application pods. The API accepts a list of URLs and initiates asynchronous background tasks.
2. **State Management (Redis):** Task states (pending, processing, completed, failed) are reliably tracked using an internal Redis cache.
3. **I/O Processing (Python/aiohttp):** Asynchronous workers download files in a streaming manner and upload them directly to Amazon S3, preventing local disk and memory overload in the cluster.
4. **Event-Driven Post-Processing (AWS Lambda):** The creation of a new file in the S3 bucket automatically triggers an isolated AWS Lambda function for metadata extraction and analytics, effectively decoupling network I/O from compute-heavy tasks.

## Tech Stack

* **Language:** Python 3.14
* **Infrastructure:** Kubernetes, Docker, Nginx Ingress Controller
* **Cloud Services:** AWS S3, AWS Lambda, IAM, CloudWatch
* **Databases:** Redis
* **Libraries:** aiohttp, aioboto3

## Prerequisites

* Docker Desktop with Kubernetes enabled.
* `kubectl` CLI tool installed.
* AWS Account (configured S3 Bucket and IAM credentials).

## Setup and Deployment

### 1. Configure Secrets
To securely interact with AWS, you need to set up Kubernetes secrets.

Copy the configuration template:
> cp k8s/aws-secret-sample.example k8s/aws-secret.yaml

Open `k8s/aws-secret.yaml` and insert your AWS credentials. **Note:** The key values must be Base64 encoded. The `aws-secret.yaml` file is added to `.gitignore` and should never be committed to version control.

### 2. Build the Docker Image
Build the local application image:
> docker build -t streamfetch-api:latest .

### 3. Deploy the Infrastructure
Apply the Kubernetes configuration manifests (Deployments, Services, Ingress, Secrets):
> kubectl apply -f k8s/

Ensure all components have transitioned to the `Running` state:
> kubectl get pods

## API Usage

### Create a Fetch Task
Send a POST request with an array of target URLs:
> curl -X POST http://localhost/api/v1/fetch \
> -H "Content-Type: application/json" \
> -d '{"urls": ["https://upload.wikimedia.org/wikipedia/commons/3/3a/Cat03.jpg"]}'

On success, the server will return a JSON response containing a unique `job_id`.

### Check Task Status
Use the received `job_id` to check the execution status:
> curl http://localhost/api/v1/status/<your_job_id>

A `"completed"` status confirms that the file was successfully downloaded and streamed to the S3 bucket.

## AWS Lambda Configuration

To complete the event-driven pipeline, configure a serverless function in the AWS Cloud. The handler source code is located in the `lambda/` directory of this repository.

1. Create a new Lambda function (Python 3.10+).
2. Assign an IAM role with the `AmazonS3ReadOnlyAccess` policy to the function.
3. Add an S3 trigger for the `All object create events` event on your bucket.
4. Deploy the code from `lambda/lambda_handler.py`. Function logs and execution results will be available in Amazon CloudWatch.