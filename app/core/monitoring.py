import time
from fastapi import Request
from loguru import logger

# In-memory storage for metrics. In a real app,  proper system like Prometheus.
METRICS = {
    "total_requests": 0,
    "crud_counts": {"create": 0, "read": 0, "update": 0, "delete": 0},
    "latencies": []
}

# Configure logger for structured JSON output
logger.remove()
logger.add(
    "server_logs.log", # Log to a file
    format="{message}",
    serialize=True,
    level="INFO",
    rotation="10 MB"
)

async def logging_middleware(request: Request, call_next):
    start_time = time.time()

    # Try to get user from the dependency that runs before this middleware
    try:
        actor_id = request.state.user.get("uid")
    except AttributeError:
        actor_id = "anonymous"

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000  # in milliseconds
    METRICS["latencies"].append(process_time)
    METRICS["total_requests"] += 1

    log_details = {
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "latency_ms": round(process_time, 2),
        "actor_id": actor_id,
    }

    # Simple logic to categorize CRUD operations
    method = request.method
    path = request.url.path
    if path.startswith("/products"):
        if method == "POST": METRICS["crud_counts"]["create"] += 1
        elif method == "GET": METRICS["crud_counts"]["read"] += 1
        elif method == "PUT": METRICS["crud_counts"]["update"] += 1
        elif method == "DELETE": METRICS["crud_counts"]["delete"] += 1

    logger.info(log_details)
    return response

def get_metrics():
    if not METRICS["latencies"]:
        p95_latency = 0
    else:
        METRICS["latencies"].sort()
        p95_index = int(len(METRICS["latencies"]) * 0.95)
        p95_latency = METRICS["latencies"][p95_index]

    return {
        "total_requests_in_run": METRICS["total_requests"],
        "crud_operation_counts": METRICS["crud_counts"],
        "p95_latency_ms": round(p95_latency, 2)
    }