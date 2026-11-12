from django.db.models import ProtectedError
from django.http import JsonResponse

from api.models import Vaga
from api.views.utils import erro, ler_json, lista, mensagem, metodo_nao_permitido, texto

TIPOS = ('CARRO', 'MOTO')
STATUSES = ('LIVRE', 'OCUPADA')


def vaga_to_dict(vaga):
    return {
        'id':     vaga.id,
        'numero': vaga.numero,
        'tipo':   vaga.tipo,
        'status': vaga.status,
    }


def _validar(dados):
    """Retorna (campos, erro_response)."""
    if dados is None:
        return None, erro('JSON inválido', 400)
    numero = texto(dados, 'numero')
    tipo = texto(dados, 'tipo')
    if not numero:
        return None, erro("Campo 'numero' é obrigatório", 400)
    if tipo not in TIPOS:
        return None, erro("Campo 'tipo' deve ser CARRO ou MOTO", 400)
    return {'numero': numero, 'tipo': tipo}, None


def lista_vagas(request):
    if request.method == 'GET':
        vagas = Vaga.objects.order_by('numero')
        status = request.GET.get('status')
        if status:
            vagas = vagas.filter(status=status)
        return lista(vagas, vaga_to_dict)

    if request.method == 'POST':
        campos, resp = _validar(ler_json(request))
        if resp:
            return resp
        if Vaga.objects.filter(numero=campos['numero']).exists():
            return erro('Número de vaga já cadastrado', 409)
        # Toda vaga nova começa LIVRE, como no Java
        vaga = Vaga.objects.create(status='LIVRE', **campos)
        return JsonResponse(vaga_to_dict(vaga), status=201)

    return metodo_nao_permitido()


def detalhe_vaga(request, id):
    if request.method not in ('GET', 'PUT', 'DELETE'):
        return metodo_nao_permitido()

    try:
        vaga = Vaga.objects.get(id=id)
    except Vaga.DoesNotExist:
        return erro('Vaga não encontrada', 404)

    if request.method == 'GET':
        return JsonResponse(vaga_to_dict(vaga))

    if request.method == 'PUT':
        dados = ler_json(request)
        campos, resp = _validar(dados)
        if resp:
            return resp
        if Vaga.objects.filter(numero=campos['numero']).exclude(id=id).exists():
            return erro('Número de vaga já cadastrado', 409)
        status = texto(dados, 'status')
        vaga.numero = campos['numero']
        vaga.tipo = campos['tipo']
        vaga.status = status if status in STATUSES else 'LIVRE'
        vaga.save()
        return JsonResponse(vaga_to_dict(vaga))

    try:
        vaga.delete()
    except ProtectedError:
        return erro('Não é possível excluir vaga com permanências registradas', 409)
    return mensagem('Vaga excluída com sucesso')
