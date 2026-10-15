"""Small middleware shared by the whole backend."""


def no_cache_for_api(get_response):
    """Every /api/ answer is personal (a student's feed, timetable, alerts): tell browsers and
    any cache in between (such as Vercel's, which forwards /api/ to Render) never to store
    it. An answer that already says how to cache itself is left alone."""

    def middleware(request):
        response = get_response(request)
        if request.path.startswith("/api/") and not response.has_header("Cache-Control"):
            response["Cache-Control"] = "private, no-store"
        return response

    return middleware
