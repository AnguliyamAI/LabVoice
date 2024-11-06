# Guide


## **1. Updated System Architecture Overview**

### **User Interaction Flow**

1. **Website Access**: User opens the website.
2. **Start Interaction**: User clicks the **Start** button to begin.
3. **Live Speech-to-Text**: User's speech is converted to text in real-time.
4. **Input to LLM**: Transcribed text is sent to the LLM on AWS Bedrock.
5. **Agentic RAG Flow**: LLM retrieves relevant SOP steps from JSON files.
6. **LLM Response**: LLM generates a response.
7. **Text-to-Speech Conversion**: Response is converted back to speech.
8. **Audio Playback**: Speech is played back to the user with minimal delay.
9. **Task Logging**: Task completions are logged in DynamoDB.
10. **Document Generation**: A summary document is generated for download.

---

## **2. Setting Up AWS Infrastructure**

Set up AWS services manually via the AWS Management Console.

### **Required AWS Services**

- **AWS Lambda**
- **Amazon DynamoDB**
- **Amazon S3**
- **AWS Bedrock**
- **Amazon API Gateway** (for real-time communication)
- **AWS Cognito** (optional for user authentication)

---

## **3. Implementing Real-Time Speech-to-Text Conversion**

### **Client-Side Live Speech Recognition**

#### **Using the Web Speech API**

 the Web Speech API for live speech recognition with minimal delay.

```javascript
// Check for browser compatibility
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {
  const recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;

  recognition.onresult = (event) => {
    let finalTranscript = '';
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript;
        // Send the final transcript to the server
        sendTextToServer(finalTranscript);
      }
    }
  };

  // Start speech recognition
  recognition.start();
} else {
  alert('Your browser does not support Speech Recognition.');
}
```


---

## **4. Sending Transcribed Text to AWS Bedrock**

### **Lambda Function: `LLMHandler`**

- Receives transcribed text from the client.
- Uses AWS Bedrock to process the text with an agentic RAG flow.
- Returns the LLM's response.

#### **Function Logic**

1. **Receive Transcribed Text**

   ```python
   user_input = event['body']['text']
   ```

2. **Retrieve Relevant SOP Steps**

   Implement a function to retrieve SOP steps from JSON files.

   ```python
   def retrieve_sop_steps(user_input):
       # Logic to retrieve relevant SOP steps from S3 or DynamoDB
       return sop_steps
   ```

3. **Prepare Prompt for LLM**

   ```python
   prompt = f"""
   You are assisting with lab SOPs. The user said: "{user_input}"
   Relevant SOP steps: {sop_steps}
   Provide a helpful and concise response.
   """
   ```

4. **Invoke AWS Bedrock LLM**

   ```python
   bedrock = boto3.client('bedrock')
   response = bedrock.invoke_model(
       modelId='your-bedrock-model-id',
       content=prompt
   )
   ai_response = response['result']
   ```

5. **Return Response**

   ```python
   return {
       'statusCode': 200,
       'body': json.dumps({'response': ai_response})
   }
   ```

---

## **5. Implementing Agentic RAG Flow**

### **Storing SOP Files in JSON Format**

#### **Sample SOP JSON Structure**

```json
{
  "sop_id": "SOP001",
  "title": "Properly Wear Gloves",
  "steps": [
    "Step 1: Wash hands thoroughly.",
    "Step 2: Select the correct glove size.",
    "Step 3: Inspect gloves for defects.",
    "Step 4: Put on gloves carefully."
  ],
  "metadata": {
    "category": "Safety",
    "created_by": "LabAdmin",
    "created_at": "2023-10-01"
  }
}
```

### **Storing SOPs in DynamoDB**

- **Table Name**: `SOPFiles`
- **Primary Key**: `sop_id` (String)

### **Retrieving SOP Steps**

Use DynamoDB queries to retrieve relevant SOPs based on user input.

```python
def retrieve_sop_steps(user_input):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('SOPFiles')
    response = table.scan(
        FilterExpression=Attr('title').contains(user_input) | Attr('steps').contains(user_input)
    )
    return response['Items']
```

---

## **6. Live Text-to-Speech Conversion**

### **Client-Side Speech Synthesis**

Utilize the Web Speech API's `SpeechSynthesis` interface for immediate feedback.

```javascript
function speakText(text) {
  const speechSynthesis = window.speechSynthesis;
  const utterance = new SpeechSynthesisUtterance(text);
  speechSynthesis.speak(utterance);
}

// After receiving the response from the server
socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  displayResponse(data.response);
  speakText(data.response);
};
```

---

## **7. Logging Task Completions and Generating Documents**

### **Logging to DynamoDB**

#### **DynamoDB Table: `TaskLogs`**

- **Primary Key**: `task_id` (String)
- **Attributes**:
  - `user_id` (String)
  - `task_details` (Map)
  - `timestamp` (Number)

#### **Lambda Function: `TaskLogger`**

Triggered when the user says "task completed".

```python
def lambda_handler(event, context):
    user_id = event['user_id']
    task_details = event['task_details']
    timestamp = int(datetime.utcnow().timestamp())
    task_id = str(uuid.uuid4())

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TaskLogs')
    table.put_item(
        Item={
            'task_id': task_id,
            'user_id': user_id,
            'task_details': task_details,
            'timestamp': timestamp
        }
    )

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Task logged successfully'})
    }
```

### **Document Generation**

#### **Lambda Function: `DocumentGenerator`**

Generates a summary document at the end of the session.

```python
def lambda_handler(event, context):
    user_id = event['user_id']
    # Retrieve task logs for the user
    # Generate a document (e.g., PDF)
    # Store the document in S3
    # Provide a download link
```

---

## **8. Client Application Updates**

### **User Interface**

- **Start Button**: Initiates speech recognition.
- **Live Transcription**: Displays real-time transcribed text.
- **Response Display**: Shows the LLM's response.
- **Download Tab**: Allows users to download the generated document.

### **Event Handling**

- **Start Button Click**: Starts speech recognition.
- **Transcription Result**: Sends final transcripts to the server.
- **Receive Response**: Displays and speaks the response.
- **Task Completion**: Detects "task completed" and triggers logging.
- **Session End**: Enables document download.

---

## **9. Real-Time Communication with API Gateway WebSockets**

### **Setting Up WebSocket API**

#### **Routes**

- **$connect**: Establishes the connection.
- **$disconnect**: Handles disconnections.
- **sendMessage**: Receives messages from the client.

### **Integrating with Lambda**

Associate the `LLMHandler` Lambda function with the `sendMessage` route.

### **Client-Side WebSocket Connection**

```javascript
const socket = new WebSocket('wss://your-api-id.execute-api.region.amazonaws.com/Prod');

socket.onopen = () => {
  console.log('WebSocket connected');
};

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  displayResponse(data.response);
  speakText(data.response);
};

function sendTextToServer(text) {
  const message = {
    action: 'sendMessage',
    user_input: text,
    user_id: 'user123'
  };
  socket.send(JSON.stringify(message));
}
```

---

## **10. Ensuring Minimal Delay**

### **Optimizations**

- **Client-Side Processing**: Use client-side APIs for speech recognition and synthesis.
- **Efficient Lambda Code**: Optimize code for performance.
- **Asynchronous Operations**: Use async processing where possible.
- **Resource Provisioning**: Allocate sufficient memory and compute resources.

---


