"""Development API entrypoint that supports whichever local port Next selects."""

from fastapi.middleware.cors import CORSMiddleware

from .entrypoint import app


app.user_middleware = [middleware for middleware in app.user_middleware if middleware.cls is not CORSMiddleware]
app.middleware_stack = None
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1|[0-9.]+):[0-9]+$",
    allow_methods=["*"],
    allow_headers=["*"],
)
