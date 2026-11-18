
# Azure Functions – Serverless Application

A beginner-friendly project demonstrating how to build a serverless backend using **Azure Functions (Python)**, connect it to a **React frontend**, and run Azure Storage locally using **Azurite**.

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | Python + Azure Functions |
| Storage Emulator | Azurite |
| Runtime | Azure Functions Core Tools v4 |
| Package Manager | npm + pip |

## Project Structure

```text
azure_functions/
│
├── backend/
│   ├── function_app.py
│   ├── host.json
│   ├── requirements.txt
│   └── local.settings.json
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── App.css
│   ├── package.json
│   ├── index.html
│   └── vite.config.js
│
└── README.md
```

## Prerequisites

Install the following tools:

- [Python 3.11](https://www.python.org/downloads/)
- [Node.js and npm](https://nodejs.org/)
- [Azure Functions Core Tools v4](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite)
- Visual Studio Code (recommended)

Verify installations:

```powershell
python --version
node --version
npm --version
func --version
```

## 1. Backend Setup

Navigate to the backend directory:

```powershell
cd backend
```

Create a Python virtual environment if you don't already have one:

```powershell
py -3.11 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start the Azure Functions backend:

```powershell
func start
```

Backend URL:

```text
http://localhost:7071
```

Test the HTTP function:

```text
http://localhost:7071/api/hello
```

## 2. Frontend Setup

Open another terminal and navigate to the frontend directory:

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

Start the React development server:

```powershell
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

The frontend communicates with the backend through the Vite development proxy configured in `vite.config.js`.

## 3. Azure Storage Setup (Azurite)

Azurite is a local emulator for Azure Storage services.

Install Azurite globally:

```powershell
npm install -g azurite
```

Start the emulator:

```powershell
azurite
```

Default local endpoints:

| Storage Service | Endpoint |
|---|---|
| Blob Storage | http://127.0.0.1:10000 |
| Queue Storage | http://127.0.0.1:10001 |
| Table Storage | http://127.0.0.1:10002 |

Keep the Azurite terminal running while developing locally.

## 4. Local Configuration

The backend uses `local.settings.json` to configure its local environment.

Example:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python"
  }
}
```

`UseDevelopmentStorage=true` tells Azure Functions to connect to the local Azurite emulator.

**Note:** `local.settings.json` contains local configuration and should not be committed to Git.

## 5. Run the Complete Application

You need three separate terminals.

### Terminal 1 – Azure Storage

```powershell
azurite
```

### Terminal 2 – Python Backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
func start
```

### Terminal 3 – React Frontend

```powershell
cd frontend
npm run dev
```

Open the application:

```text
http://localhost:5173
```

## 6. Application Architecture

```text
                User
                  |
                  v
          React Frontend
          localhost:5173
                  |
                  | HTTP Request
                  v
          Vite Development Proxy
                  |
                  v
         Python Azure Functions
          localhost:7071
                  |
                  v
           Azure Storage
              Azurite
                  |
          -----------------
          |       |       |
         Blob   Queue   Table
```

**Important:** The current `/api/hello` function returns a JSON response and does not yet perform any storage operations. Azurite is configured and ready for future storage integration.

## 7. Important Development URLs

| Component | URL |
|---|---|
| React Frontend | http://localhost:5173 |
| Azure Functions Host | http://localhost:7071 |
| Hello API | http://localhost:7071/api/hello |
| Azurite Blob | http://127.0.0.1:10000 |
| Azurite Queue | http://127.0.0.1:10001 |
| Azurite Table | http://127.0.0.1:10002 |

## 8. Future Enhancements

- Integrate Azure Blob Storage for file uploads.
- Implement Azure Queue Storage triggers.
- Add more HTTP-triggered Azure Functions.
- Connect frontend file uploads to Blob Storage.
- Deploy the backend to Azure Functions.
- Deploy the frontend separately using an appropriate hosting service.
- Configure Azure Storage in the cloud instead of using Azurite.

## Learning Objective

Understand serverless computing and how to separate frontend and backend responsibilities using Azure Functions, while integrating Azure Storage services for scalable application development.

# Python
.venv/
__pycache__/
*.pyc

# Azure Functions local settings
backend/local.settings.json

# Node
frontend/node_modules/
frontend/dist/

# Environment files
.env
.env.*