from backend_bridge import BackendEventPublisher

publisher = BackendEventPublisher()

ok = publisher.publish(
    "LOG",
    {
        "level": "INFO",
        "message": "Hello from the simulation process!",
    },
)

print("Backend publish:", "PASS" if ok else "FAIL")
