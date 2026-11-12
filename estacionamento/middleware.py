from django.http import HttpResponse

CORS_HEADERS = {
    'Access-Control-Allow-Origin':  '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
}


class CorsMiddleware:
    """Injeta os cabeçalhos CORS em todas as respostas e responde o preflight OPTIONS."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'OPTIONS':
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        for header, valor in CORS_HEADERS.items():
            response[header] = valor
        return response
