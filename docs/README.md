
## **1. Set Up the AWS Infrastructure Without CI/CD, Cognito, and CloudWatch**

### **a. Create AWS Resources Manually**

Since we're not using AWS CloudFormation or AWS CDK, we'll set up the AWS resources manually via the AWS Management Console.

#### **Required AWS Services:**

- **AWS Lambda**
- **Amazon DynamoDB**
- **Amazon S3**
- **Amazon API Gateway**

---

## **2. Define the Lambda Functions Using Python**

We'll create the Lambda functions in Python, containerized with Docker for consistency and ease of deployment.

### **a. Install Necessary Tools**

- **Python 3.8 or later**
- **Docker**
- **AWS CLI**
- **AWS SAM CLI (optional but recommended for local testing)**

### **b. Lambda Functions Overview**

1. **`VoiceCommandHandler`**: Processes voice commands from the client application.
2. **`SOPManager`**: Manages CRUD operations for Standard Operating Procedures (SOPs).
3. **`AuditTrailLogger`**: Logs events related to SOP execution and user actions.
4. **`SettingsManager`**: Manages user settings and preferences.
5. **`SpeechProcessing`**: Handles speech-to-text and text-to-speech functionalities using Whisper.

### **c. Create Dockerfiles for Each Lambda Function**

For each Lambda function:

1. **Create a Directory**:

   ```bash
   mkdir VoiceCommandHandler
   cd VoiceCommandHandler
   ```

2. **Create a Dockerfile**:

   ```dockerfile
   FROM public.ecr.aws/lambda/python:3.8

   # Install necessary Python packages
   RUN pip install boto3 langchain openai-whisper

   # Copy function code
   COPY app.py ${LAMBDA_TASK_ROOT}

   # Set the CMD to your handler (app.lambda_handler)
   CMD ["app.lambda_handler"]
   ```

3. **Write the Lambda Function Code (`app.py`)**

   ```python
   import json
   import boto3
   # Additional imports for LangChain and Whisper

   def lambda_handler(event, context):
       # Process the voice command
       # Use Whisper for speech-to-text
       # Use LangChain for natural language processing
       # Return the response
       return {
           'statusCode': 200,
           'body': json.dumps('Voice command processed successfully.')
       }
   ```

4. **Build the Docker Image**

   ```bash
   docker build -t voicecommandhandler .
   ```

5. **Repeat the Steps for Other Lambda Functions**

---

## **3. Set Up DynamoDB Tables**

### **a. Create DynamoDB Tables via AWS Console**

1. **`SOPs` Table**:

   - **Primary Key**: `SOPId` (String)

2. **`AuditTrail` Table**:

   - **Primary Key**: `AuditId` (String)
   - **Sort Key**: `Timestamp` (Number)

3. **`UserSettings` Table**:

   - **Primary Key**: `UserId` (String)

---

## **4. Set Up the S3 Bucket**

### **a. Create an S3 Bucket**

1. Go to the **S3** service in AWS Console.
2. Click on **"Create bucket"**.
3. Enter a unique bucket name, e.g., `labvoice-audio-files`.
4. Choose the region.
5. Disable public access (for security).
6. Click **"Create bucket"**.

---

## **5. Configure the API Gateway**

### **a. Create a REST API**

1. Go to the **API Gateway** service.
2. Click on **"Create API"** > **REST API** > **Build**.
3. Choose **"New API"**.
4. Enter **API Name**, e.g., `LabVoiceAPI`.
5. Click **"Create API"**.

### **b. Create Resources and Methods**

1. **Voice Command Resource**:

   - Resource Path: `/voicecommand`
   - Method: `POST`
   - Integration Type: **Lambda Function** (`VoiceCommandHandler`)

2. **SOP Management Resource**:

   - Resource Path: `/sop`
   - Methods: `GET`, `POST`, `PUT`, `DELETE`
   - Integration Type: **Lambda Function** (`SOPManager`)

3. **Audit Trail Resource**:

   - Resource Path: `/audittrail`
   - Method: `GET`
   - Integration Type: **Lambda Function** (`AuditTrailLogger`)

4. **Settings Resource**:

   - Resource Path: `/settings`
   - Methods: `GET`, `PUT`
   - Integration Type: **Lambda Function** (`SettingsManager`)

### **c. Deploy the API**

1. Click on **"Actions"** > **"Deploy API"**.
2. Create a new stage, e.g., `prod`.
3. Note the **Invoke URL** for testing.

---

## **6. Implement the Lambda Functions with Python and LangChain**

### **a. `VoiceCommandHandler` Implementation**

1. **Speech-to-Text with Whisper**:

   - Use the Whisper model to transcribe audio input.
   - Install Whisper:

     ```bash
     pip install openai-whisper
     ```

2. **Natural Language Processing with LangChain**:

   - Use LangChain to interpret the transcribed text and determine the action.
   - Install LangChain:

     ```bash
     pip install langchain
     ```

3. **Function Logic**:

   ```python
   import json
   import whisper
   from langchain import LLMChain
   # Additional imports

   def lambda_handler(event, context):
       # Extract audio file from the event
       # Transcribe audio using Whisper
       # Process transcription with LangChain
       # Determine the appropriate action (e.g., execute an SOP)
       # Return response
   ```

### **b. `SOPManager` Implementation**

1. **CRUD Operations**:

   - Use `boto3` to interact with the `SOPs` DynamoDB table.
   - Implement functions to create, read, update, and delete SOPs.

2. **Function Logic**:

   ```python
   import json
   import boto3

   dynamodb = boto3.resource('dynamodb')
   table = dynamodb.Table('SOPs')

   def lambda_handler(event, context):
       http_method = event['httpMethod']
       if http_method == 'GET':
           # Retrieve SOPs
       elif http_method == 'POST':
           # Create a new SOP
       # Handle other methods
   ```

### **c. `AuditTrailLogger` Implementation**

1. **Logging Actions**:

   - Whenever an SOP is executed or a user action occurs, log the event.
   - Use `boto3` to store logs in the `AuditTrail` DynamoDB table.

2. **Function Logic**:

   ```python
   import json
   import boto3
   from datetime import datetime

   dynamodb = boto3.resource('dynamodb')
   table = dynamodb.Table('AuditTrail')

   def log_event(action, details):
       table.put_item(
           Item={
               'AuditId': str(uuid.uuid4()),
               'Timestamp': int(datetime.now().timestamp()),
               'Action': action,
               'Details': details
           }
       )

   def lambda_handler(event, context):
       # Parse event
       # Log the action
       # Return response
   ```

### **d. `SettingsManager` Implementation**

1. **Manage User Settings**:

   - Use `boto3` to interact with the `UserSettings` DynamoDB table.
   - Allow getting and updating user settings.

2. **Function Logic**:

   ```python
   import json
   import boto3

   dynamodb = boto3.resource('dynamodb')
   table = dynamodb.Table('UserSettings')

   def lambda_handler(event, context):
       http_method = event['httpMethod']
       if http_method == 'GET':
           # Retrieve user settings
       elif http_method == 'PUT':
           # Update user settings
       # Handle other methods
   ```

### **e. `SpeechProcessing` Implementation**

Since speech-to-text is handled in `VoiceCommandHandler`, `SpeechProcessing` can focus on text-to-speech.

1. **Text-to-Speech Conversion**:

   - Use a TTS library like `pyttsx3` or integrate with Amazon Polly (requires AWS SDK).
   - Install `pyttsx3`:

     ```bash
     pip install pyttsx3
     ```

2. **Function Logic**:

   ```python
   import pyttsx3
   import boto3

   s3 = boto3.client('s3')
   bucket_name = 'labvoice-audio-files'

   def lambda_handler(event, context):
       text = event['text']
       # Convert text to speech
       engine = pyttsx3.init()
       engine.save_to_file(text, '/tmp/output.mp3')
       engine.runAndWait()
       # Upload audio file to S3
       s3.upload_file('/tmp/output.mp3', bucket_name, 'output.mp3')
       # Return S3 URL
   ```

---

## **7. Package and Deploy Lambda Functions Using Docker**

### **a. Build Docker Images**

For each Lambda function:

```bash
docker build -t function_name .
```

### **b. Create ECR Repository and Push Images**

1. **Create ECR Repository**:

   ```bash
   aws ecr create-repository --repository-name function_name
   ```

2. **Authenticate Docker to ECR**:

   ```bash
   aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin your-account-id.dkr.ecr.your-region.amazonaws.com
   ```

3. **Tag and Push Image**:

   ```bash
   docker tag function_name:latest your-account-id.dkr.ecr.your-region.amazonaws.com/function_name:latest
   docker push your-account-id.dkr.ecr.your-region.amazonaws.com/function_name:latest
   ```

### **c. Create Lambda Functions Using ECR Images**

1. Go to **AWS Lambda** in the AWS Console.
2. Click **"Create function"**.
3. Choose **"Container image"**.
4. Select the image from ECR.
5. Configure function settings:

   - **Function name**: `VoiceCommandHandler`, etc.
   - **Runtime**: Python 3.8
   - **Role**: Create or select an IAM role with necessary permissions.

6. Click **"Create function"**.

### **d. Set Up Environment Variables and Permissions**

1. **Environment Variables**:

   - Set any necessary environment variables, such as table names, bucket names, etc.

2. **IAM Roles**:

   - Ensure the Lambda function's execution role has permissions to access:

     - DynamoDB tables
     - S3 bucket
     - Any other required AWS services

---

## **8. Finalize API Gateway Integration**

Ensure that each API Gateway method is correctly linked to the corresponding Lambda function.

- **Method Request**:

  - No authorization (since we're not using Cognito)

- **Integration Request**:

  - Lambda Proxy Integration: **Enabled**

- **Deployment**:

  - Redeploy the API if any changes were made.

---

## **9. Test the Deployed Application**

### **a. Functional Testing**

1. **Voice Command Execution**:

   - Use a tool like **Postman** to simulate API calls.
   - For the `/voicecommand` endpoint, send an audio file in the request body.
   - Verify that the response is as expected.

2. **SOP Management**:

   - Test CRUD operations via the `/sop` endpoint.
   - Ensure data is correctly stored and retrieved from DynamoDB.

3. **Audit Trail Logging**:

   - Execute actions that should trigger logs.
   - Check the `AuditTrail` table to verify entries.

4. **Settings Management**:

   - Get and update settings via the `/settings` endpoint.
   - Confirm changes in the `UserSettings` table.

5. **Speech Processing**:

   - Test text-to-speech conversion.
   - Verify that the audio file is stored in S3 and accessible.

### **b. End-to-End Testing**

- Simulate a user speaking a command to execute an SOP.
- Ensure the system processes the speech, interprets the command, executes the SOP, and provides a spoken response.

---

## **10. Develop a Basic Client Application **

### **a. Web-Based Client**

1. **Technologies**:

   - **HTML/CSS/JavaScript**
   - **Web Audio API** for recording audio
   - **Fetch API** for making HTTP requests

2. **Features**:

   - Record voice input and send to `/voicecommand`.
   - Play audio responses received from the application.

