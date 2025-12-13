# Installation Instructions

To enable rate limiting features, install the following dependencies:

```bash
pip install slowapi
```

This will automatically install required sub-dependencies (`limits`, etc.).

## Configuration

Rate limiting is configured to use in-memory storage by default, which is suitable for single-instance deployments (like the current Railway setup).

If scaling to multiple instances, you must update `app/limiter.py` to use a Redis or Memcached backend:

```python
limiter = Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379")
```
