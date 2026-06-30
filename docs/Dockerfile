FROM squidfunk/mkdocs-material
RUN pip install mkdocstrings[python]
ENTRYPOINT []
CMD ["sh", "-c", "mkdocs build --site-dir /tmp/site && python -m http.server 8000 --directory /tmp/site"]
