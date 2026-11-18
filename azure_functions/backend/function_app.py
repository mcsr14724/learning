import azure.functions as func
import json
from datetime import datetime, timezone

app = func.FunctionApp()

@app.route(
    route="hello",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS
)
def hello(req: func.HttpRequest):

    response = {
        "message": "Hello from Azure Functions!",
        "backend": "Python",
        "architecture": "Serverless",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    return func.HttpResponse(
        json.dumps(response),
        status_code=200,
        mimetype="application/json"
    )