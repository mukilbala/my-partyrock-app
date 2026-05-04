import json, os, boto3
from flask import Flask, request, Response, stream_with_context

app = Flask(__name__)
bedrock = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION","us-east-1"))
MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
}

@app.route("/", methods=["OPTIONS"])
def options():
    return Response("", status=200, headers=CORS)

@app.route("/", methods=["POST"])
def generate():
    data = request.get_json(force=True, silent=True) or {}
    prompt = data.get("prompt", "")
    content = []
    file_data = data.get("file_data")
    file_mime = data.get("file_mime", "")
    if file_data:
        if file_mime.startswith("image/"):
            fmt = file_mime.split("/")[-1]
            if fmt == "jpg": fmt = "jpeg"
            content.append({"type":"image","source":{"type":"base64","media_type":file_mime,"data":file_data}})
        else:
            content.append({"type":"document","source":{"type":"base64","media_type":file_mime,"data":file_data}})
    content.append({"type":"text","text":prompt})
    messages = [{"role":"user","content":content}]
    body = json.dumps({"anthropic_version":"bedrock-2023-05-31","max_tokens":4096,"messages":messages})

    def stream():
        try:
            r = bedrock.invoke_model_with_response_stream(
                modelId=MODEL_ID, body=body,
                contentType="application/json", accept="application/json")
            for event in r["body"]:
                chunk = event.get("chunk")
                if chunk:
                    d = json.loads(chunk["bytes"].decode("utf-8"))
                    if d.get("type") == "content_block_delta":
                        delta = d.get("delta", {})
                        if delta.get("type") == "text_delta":
                            yield delta.get("text", "")
        except Exception as e:
            yield "\n\nError: " + str(e)

    resp = Response(stream_with_context(stream()), content_type="text/plain; charset=utf-8")
    for k, v in CORS.items():
        resp.headers[k] = v
    return resp

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
