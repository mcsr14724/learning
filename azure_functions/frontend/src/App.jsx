
import { useState } from "react";
import "./App.css";

const API = "/api";

function App() {
  const [httpResult, setHttpResult] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadResult, setUploadResult] = useState("");
  const [queueMessage, setQueueMessage] = useState("");
  const [queueResult, setQueueResult] = useState("");
  const [loading, setLoading] = useState(false);

  // HTTP Trigger
  const callHttpTrigger = async () => {
    setLoading(true);
    setHttpResult("");

    try {
      const response = await fetch(`${API}/hello`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Request failed");
      }

      setHttpResult(JSON.stringify(data, null, 2));
    } catch (error) {
      setHttpResult(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Blob Trigger: Upload file through backend
  const uploadFile = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setUploadResult("");

    try {
      const base64Content = await new Promise((resolve, reject) => {
        const reader = new FileReader();

        reader.onload = () => {
          resolve(reader.result.split(",")[1]);
        };

        reader.onerror = () => reject(new Error("Unable to read file"));

        reader.readAsDataURL(selectedFile);
      });

      const response = await fetch(`${API}/upload`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          filename: selectedFile.name,
          content: base64Content,
          contentType:
            selectedFile.type || "application/octet-stream",
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Upload failed");
      }

      setUploadResult(
        `${data.message}\nFile: ${data.filename}\nContainer: ${data.container}\n\nCheck backend logs for Blob Trigger execution.`
      );
    } catch (error) {
      setUploadResult(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Queue Trigger: Send message through backend
  const sendQueueMessage = async () => {
    if (!queueMessage.trim()) return;

    setLoading(true);
    setQueueResult("");

    try {
      const response = await fetch(`${API}/enqueue`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: queueMessage,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Queue operation failed");
      }

      setQueueResult(
        `${data.message}\nQueue: ${data.queue}\n\nCheck backend logs for Queue Trigger execution.`
      );

      setQueueMessage("");
    } catch (error) {
      setQueueResult(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="dashboard">
      <header className="header">
        <div>
          <p className="eyebrow">SERVERLESS DEVELOPMENT</p>
          <h1>Azure Functions Dashboard</h1>
          <p className="subtitle">
            Test HTTP, Blob, Queue and Timer triggers.
          </p>
        </div>

        <span className="status">Local Development</span>
      </header>

      <section className="trigger-grid">

        {/* HTTP Trigger */}
        <article className="trigger-card">
          <div className="card-heading">
            <span className="trigger-icon">🌐</span>
            <span className="trigger-type">HTTP TRIGGER</span>
          </div>

          <h2>HTTP Request</h2>
          <p>Execute a function through an HTTP request.</p>

          <button onClick={callHttpTrigger} disabled={loading}>
            Call HTTP Function
          </button>

          {httpResult && <pre className="result">{httpResult}</pre>}
        </article>

        {/* Blob Trigger */}
        <article className="trigger-card">
          <div className="card-heading">
            <span className="trigger-icon">📁</span>
            <span className="trigger-type">BLOB TRIGGER</span>
          </div>

          <h2>Blob Storage</h2>
          <p>
            Upload a file to Blob Storage and activate the Blob Trigger.
          </p>

          <input
            type="file"
            onChange={(event) =>
              setSelectedFile(event.target.files?.[0] || null)
            }
          />

          {selectedFile && (
            <p className="selected-file">
              Selected: {selectedFile.name}
            </p>
          )}

          <button
            onClick={uploadFile}
            disabled={loading || !selectedFile}
          >
            Upload File
          </button>

          {uploadResult && <pre className="result">{uploadResult}</pre>}
        </article>

        {/* Queue Trigger */}
        <article className="trigger-card">
          <div className="card-heading">
            <span className="trigger-icon">📨</span>
            <span className="trigger-type">QUEUE TRIGGER</span>
          </div>

          <h2>Queue Storage</h2>
          <p>
            Send a message to Queue Storage for background processing.
          </p>

          <textarea
            placeholder="Enter a queue message..."
            value={queueMessage}
            onChange={(event) => setQueueMessage(event.target.value)}
          />

          <button
            onClick={sendQueueMessage}
            disabled={loading || !queueMessage.trim()}
          >
            Send Queue Message
          </button>

          {queueResult && <pre className="result">{queueResult}</pre>}
        </article>

        {/* Timer Trigger */}
        <article className="trigger-card">
          <div className="card-heading">
            <span className="trigger-icon">⏰</span>
            <span className="trigger-type">TIMER TRIGGER</span>
          </div>

          <h2>Scheduled Execution</h2>
          <p>
            The timer function executes automatically. It does not
            require a frontend request.
          </p>

          <div className="schedule">
            <span>Execution schedule</span>
            <strong>Every minute</strong>
            <code>0 */1 * * * *</code>
          </div>

          <p className="hint">
            Observe timer execution in the backend terminal.
          </p>
        </article>

      </section>

      <footer>
        React + Python + Azure Functions + Azurite
      </footer>
    </main>
  );
}

export default App;
