"""Funções auxiliares compartilhadas pelas views (equivalente ao HttpUtil/JsonUtil do Java)."""
import json

from django.http import JsonResponse


def erro(mensagem, status):
    return JsonResponse({'error': mensagem}, status=status)


def mensagem(texto, status=200):
    return JsonResponse({'message': texto}, status=status)


def metodo_nao_permitido():
    return erro('Método não permitido', 405)


def ler_json(request):
    """Lê o corpo da requisição como dict. Retorna None se o JSON for inválido."""
    if not request.body:
        return {}
    try:
        dados = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return None
    return dados if isinstance(dados, dict) else None


def texto(dados, campo):
    """Retorna o campo como string sem espaços nas pontas, ou None se ausente/vazio."""
    valor = dados.get(campo)
    if valor is None:
        return None
    valor = str(valor).strip()
    return valor or None


def inteiro(dados, campo):
    """Retorna o campo como int, ou None se ausente/inválido."""
    valor = dados.get(campo)
    if isinstance(valor, bool):
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def lista(itens, to_dict):
    # safe=False permite retornar uma lista JSON na raiz
    return JsonResponse([to_dict(i) for i in itens], safe=False)


def endpoint_nao_encontrado(request, *args, **kwargs):
    return erro('Endpoint não encontrado', 404)
