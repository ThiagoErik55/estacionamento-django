from django.http import JsonResponse

from api.models import Permanencia
from api.services import permanencia_service
from api.services.permanencia_service import RecursoNaoEncontrado
from api.views.utils import erro, inteiro, ler_json, lista, metodo_nao_permitido


def _iso(dt):
    return dt.isoformat() if dt else None


def permanencia_to_dict(p):
    return {
        'id':              p.id,
        'veiculoId':       p.veiculo_id,
        'veiculoPlaca':    p.veiculo.placa,
        'veiculoModelo':   p.veiculo.modelo,
        'vagaId':          p.vaga_id,
        'vagaNumero':      p.vaga.numero,
        'dataHoraEntrada': _iso(p.data_hora_entrada),
        'dataHoraSaida':   _iso(p.data_hora_saida),
        # Decimal vira string ("10.00") para não perder precisão; o frontend usa parseFloat
        'valorTotal':      str(p.valor_total) if p.valor_total is not None else None,
        'status':          p.status,
    }


def _buscar(id):
    return Permanencia.objects.select_related('veiculo', 'vaga').get(id=id)


def _executar(acao, *args, status_ok):
    try:
        permanencia = acao(*args)
    except RecursoNaoEncontrado as e:
        return erro(str(e), 404)
    except ValueError as e:
        return erro(str(e), 409)
    return JsonResponse(permanencia_to_dict(_buscar(permanencia.id)), status=status_ok)


def lista_permanencias(request):
    if request.method != 'GET':
        return metodo_nao_permitido()
    permanencias = Permanencia.objects.select_related('veiculo', 'vaga').order_by('-data_hora_entrada')
    status = request.GET.get('status')
    if status:
        permanencias = permanencias.filter(status=status)
    return lista(permanencias, permanencia_to_dict)


def entrada(request):
    if request.method != 'POST':
        return metodo_nao_permitido()
    dados = ler_json(request)
    if dados is None:
        return erro('JSON inválido', 400)
    veiculo_id = inteiro(dados, 'veiculoId')
    vaga_id = inteiro(dados, 'vagaId')
    if veiculo_id is None or vaga_id is None:
        return erro("Campos 'veiculoId' e 'vagaId' são obrigatórios", 400)
    return _executar(permanencia_service.registrar_entrada, veiculo_id, vaga_id, status_ok=201)


def saida(request, id):
    if request.method != 'PUT':
        return metodo_nao_permitido()
    return _executar(permanencia_service.registrar_saida, id, status_ok=200)
