from django.db.models import ProtectedError
from django.http import JsonResponse

from api.models import Cliente, Veiculo
from api.views.utils import erro, inteiro, ler_json, lista, mensagem, metodo_nao_permitido, texto


def veiculo_to_dict(veiculo):
    return {
        'id':          veiculo.id,
        'placa':       veiculo.placa,
        'marca':       veiculo.marca,
        'modelo':      veiculo.modelo,
        'cor':         veiculo.cor,
        'clienteId':   veiculo.cliente_id,
        'clienteNome': veiculo.cliente.nome,
    }


def _validar(dados):
    """Retorna (campos, erro_response)."""
    if dados is None:
        return None, erro('JSON inválido', 400)
    campos = {}
    for campo in ('placa', 'marca', 'modelo', 'cor'):
        valor = texto(dados, campo)
        if not valor:
            return None, erro(f"Campo '{campo}' é obrigatório", 400)
        campos[campo] = valor
    cliente_id = inteiro(dados, 'clienteId')
    if cliente_id is None:
        return None, erro("Campo 'clienteId' é obrigatório", 400)
    if not Cliente.objects.filter(id=cliente_id).exists():
        return None, erro('Cliente não encontrado', 404)
    campos['cliente_id'] = cliente_id
    return campos, None


def _buscar(id):
    return Veiculo.objects.select_related('cliente').get(id=id)


def lista_veiculos(request):
    if request.method == 'GET':
        veiculos = Veiculo.objects.select_related('cliente').order_by('placa')
        return lista(veiculos, veiculo_to_dict)

    if request.method == 'POST':
        campos, resp = _validar(ler_json(request))
        if resp:
            return resp
        if Veiculo.objects.filter(placa=campos['placa']).exists():
            return erro('Placa já cadastrada', 409)
        veiculo = Veiculo.objects.create(**campos)
        return JsonResponse(veiculo_to_dict(_buscar(veiculo.id)), status=201)

    return metodo_nao_permitido()


def detalhe_veiculo(request, id):
    if request.method not in ('GET', 'PUT', 'DELETE'):
        return metodo_nao_permitido()

    try:
        veiculo = _buscar(id)
    except Veiculo.DoesNotExist:
        return erro('Veículo não encontrado', 404)

    if request.method == 'GET':
        return JsonResponse(veiculo_to_dict(veiculo))

    if request.method == 'PUT':
        campos, resp = _validar(ler_json(request))
        if resp:
            return resp
        if Veiculo.objects.filter(placa=campos['placa']).exclude(id=id).exists():
            return erro('Placa já cadastrada', 409)
        for campo, valor in campos.items():
            setattr(veiculo, campo, valor)
        veiculo.save()
        return JsonResponse(veiculo_to_dict(_buscar(id)))

    try:
        veiculo.delete()
    except ProtectedError:
        return erro('Não é possível excluir veículo com permanências registradas', 409)
    return mensagem('Veículo excluído com sucesso')
