import { useState } from "react";
import "./App.css";

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const callBackend = async () => {
    setLoading(true);

    try {
      const response = await fetch("/api/hello");

      if (!response.ok) {
        throw new Error("Request failed");
      }

      const result = await response.json();
      setData(result);
    } catch (error) {
      console.error(error);
      alert("Unable to connect to Azure Functions");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Azure Functions Demo</h1>

      <p>React Frontend + Python Serverless Backend</p>

      <button onClick={callBackend} disabled={loading}>
        {loading ? "Calling Backend..." : "Call Azure Function"}
      </button>

      {data && (
        <div className="result">
          <h3>Backend Response</h3>
          <pre>{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default App;