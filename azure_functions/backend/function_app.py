
import azure.functions as func
import json
import logging
import os
import base64

from datetime import datetime, timezone
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.storage.queue import QueueClient
from azure.core.exceptions import ResourceExistsError

app = func.FunctionApp()

# Local Azurite configuration
CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

CONTAINER_NAME = "samples-workitems"
QUEUE_NAME = "tasks"


# --------------------------------------------------
# 1. HTTP TRIGGER
# --------------------------------------------------

@app.route(
    route="hello",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS
)
def hello(req: func.HttpRequest):

    response = {
        "message": "Hello from Azure Functions!",
        "trigger": "HTTP",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    return func.HttpResponse(
        json.dumps(response),
        status_code=200,
        mimetype="application/json"
    )


# --------------------------------------------------
# 2. BLOB TRIGGER
# --------------------------------------------------

@app.blob_trigger(
    arg_name="myblob",
    path="samples-workitems/{name}",
    connection="AzureWebJobsStorage"
)
def blob_trigger(myblob: func.InputStream):

    logging.info("BLOB TRIGGER EXECUTED")

    logging.info("Blob name: %s", myblob.name)
    logging.info("Blob size: %s bytes", myblob.length)


# --------------------------------------------------
# 3. QUEUE TRIGGER
# --------------------------------------------------

@app.queue_trigger(
    arg_name="msg",
    queue_name="tasks",
    connection="AzureWebJobsStorage"
)
def queue_trigger(msg: func.QueueMessage):

    message = msg.get_body().decode("utf-8")

    logging.info("QUEUE TRIGGER EXECUTED")
    logging.info("Message received: %s", message)


# --------------------------------------------------
# 4. TIMER TRIGGER
# --------------------------------------------------

@app.timer_trigger(
    schedule="0 */1 * * * *",
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=True
)
def timer_trigger(myTimer: func.TimerRequest):

    logging.info("TIMER TRIGGER EXECUTED")

    logging.info(
        "Current UTC time: %s",
        datetime.now(timezone.utc).isoformat()
    )


# --------------------------------------------------
# 5. HTTP API: UPLOAD FILE TO BLOB STORAGE
# --------------------------------------------------

@app.route(
    route="upload",
    methods=["POST"],
    auth_level=func.AuthLevel.ANONYMOUS
)
def upload_file(req: func.HttpRequest):

    try:
        body = req.get_json()

        filename = os.path.basename(body["filename"])
        file_data = base64.b64decode(body["content"], validate=True)
        content_type = body.get(
            "contentType",
            "application/octet-stream"
        )

        blob_service = BlobServiceClient.from_connection_string(
            CONNECTION_STRING,
            api_version="2026-06-06"
        )

        container_client = blob_service.get_container_client(
            CONTAINER_NAME
        )

        try:
            container_client.create_container()
        except ResourceExistsError:
            pass

        blob_client = container_client.get_blob_client(filename)

        blob_client.upload_blob(
            file_data,
            overwrite=True,
            content_settings=ContentSettings(
                content_type=content_type
            )
        )

        return func.HttpResponse(
            json.dumps({
                "message": "File uploaded successfully",
                "filename": filename,
                "container": CONTAINER_NAME
            }),
            status_code=200,
            mimetype="application/json"
        )

    except Exception:
        logging.exception("Blob upload failed")

        return func.HttpResponse(
            json.dumps({"error": "File upload failed"}),
            status_code=500,
            mimetype="application/json"
        )


# --------------------------------------------------
# 6. HTTP API: SEND MESSAGE TO QUEUE STORAGE
# --------------------------------------------------


@app.route(
    route="enqueue",
    methods=["POST"],
    auth_level=func.AuthLevel.ANONYMOUS
)
def enqueue_message(req: func.HttpRequest):

    try:
        body = req.get_json()
        message = body.get("message", "").strip()

        if not message:
            return func.HttpResponse(
                json.dumps({"error": "Message cannot be empty"}),
                status_code=400,
                mimetype="application/json"
            )

        queue_client = QueueClient.from_connection_string(
            CONNECTION_STRING,
            queue_name=QUEUE_NAME,
            api_version="2026-06-06"
        )

        try:
            queue_client.create_queue()
        except ResourceExistsError:
            pass

        encoded_message = base64.b64encode(
            message.encode("utf-8")
        ).decode("utf-8")

        queue_client.send_message(encoded_message)

        return func.HttpResponse(
            json.dumps({
                "message": "Message added to queue successfully",
                "queue": QUEUE_NAME
            }),
            status_code=200,
            mimetype="application/json"
        )

    except Exception:
        logging.exception("Queue operation failed")

        return func.HttpResponse(
            json.dumps({"error": "Queue operation failed"}),
            status_code=500,
            mimetype="application/json"
        )