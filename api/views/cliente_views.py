from django.db.models import ProtectedError
from django.http import JsonResponse

from api.models import Cliente
from api.views.utils import erro, ler_json, lista, mensagem, metodo_nao_permitido, texto


def cliente_to_dict(cliente):
    return {
        'id':       cliente.id,
        'nome':     cliente.nome,
        'cpf':      cliente.cpf,
        'telefone': cliente.telefone,
        'email':    cliente.email,
    }


def _validar(dados):
    """Retorna (campos, erro_response)."""
    if dados is None:
        return None, erro('JSON inválido', 400)
    nome = texto(dados, 'nome')
    cpf = texto(dados, 'cpf')
    if not nome:
        return None, erro("Campo 'nome' é obrigatório", 400)
    if not cpf:
        return None, erro("Campo 'cpf' é obrigatório", 400)
    return {
        'nome':     nome,
        'cpf':      cpf,
        'telefone': dados.get('telefone'),
        'email':    dados.get('email'),
    }, None


def lista_clientes(request):
    if request.method == 'GET':
        return lista(Cliente.objects.order_by('nome'), cliente_to_dict)

    if request.method == 'POST':
        campos, resp = _validar(ler_json(request))
        if resp:
            return resp
        if Cliente.objects.filter(cpf=campos['cpf']).exists():
            return erro('CPF já cadastrado', 409)
        cliente = Cliente.objects.create(**campos)
        return JsonResponse(cliente_to_dict(cliente), status=201)

    return metodo_nao_permitido()


def detalhe_cliente(request, id):
    if request.method not in ('GET', 'PUT', 'DELETE'):
        return metodo_nao_permitido()

    try:
        cliente = Cliente.objects.get(id=id)
    except Cliente.DoesNotExist:
        return erro('Cliente não encontrado', 404)

    if request.method == 'GET':
        return JsonResponse(cliente_to_dict(cliente))

    if request.method == 'PUT':
        campos, resp = _validar(ler_json(request))
        if resp:
            return resp
        if Cliente.objects.filter(cpf=campos['cpf']).exclude(id=id).exists():
            return erro('CPF já cadastrado', 409)
        for campo, valor in campos.items():
            setattr(cliente, campo, valor)
        cliente.save()
        return JsonResponse(cliente_to_dict(cliente))

    # DELETE: veículos do cliente são apagados em cascata,
    # mas veículos com permanências estão protegidos
    try:
        cliente.delete()
    except ProtectedError:
        return erro('Não é possível excluir cliente com veículos cadastrados', 409)
    return mensagem('Cliente excluído com sucesso')
