def public_api_only(endpoints):
    return [
        (path, path_regex, method, callback)
        for path, path_regex, method, callback in endpoints
        if path.startswith("/api/v1/")
    ]
