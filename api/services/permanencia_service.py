"""Regras de negócio de entrada e saída de veículos (equivalente ao PermanenciaService.java)."""
import math
from datetime import datetime
from decimal import Decimal

from django.db import transaction

from api.models import Permanencia, Vaga, Veiculo

TARIFA_POR_HORA = Decimal('5.00')


class RecursoNaoEncontrado(ValueError):
    """Recurso inexistente: a view responde 404. Demais ValueError viram 409."""


@transaction.atomic
def registrar_entrada(veiculo_id, vaga_id):
    # 1. Veículo não pode ter permanência em aberto
    if not Veiculo.objects.filter(id=veiculo_id).exists():
        raise RecursoNaoEncontrado('Veículo não encontrado.')
    if Permanencia.objects.filter(veiculo_id=veiculo_id, status='ABERTO').exists():
        raise ValueError('Veículo já possui uma permanência em aberto.')

    # 2. Vaga precisa existir e estar livre
    try:
        vaga = Vaga.objects.get(id=vaga_id)
    except Vaga.DoesNotExist:
        raise RecursoNaoEncontrado('Vaga não encontrada.')
    if vaga.status != 'LIVRE':
        raise ValueError('Vaga já está ocupada.')

    # 3. Ocupa a vaga
    vaga.status = 'OCUPADA'
    vaga.save()

    # 4. Cria a permanência
    return Permanencia.objects.create(
        veiculo_id=veiculo_id,
        vaga=vaga,
        data_hora_entrada=datetime.now(),
        status='ABERTO',
    )


@transaction.atomic
def registrar_saida(permanencia_id):
    # 1. Permanência precisa existir e estar aberta
    try:
        permanencia = Permanencia.objects.select_related('vaga').get(id=permanencia_id)
    except Permanencia.DoesNotExist:
        raise RecursoNaoEncontrado('Permanência não encontrada.')
    if permanencia.status != 'ABERTO':
        raise ValueError('Permanência já foi finalizada.')

    # 2. Calcula o valor
    saida = datetime.now()
    valor = _calcular_valor(permanencia.data_hora_entrada, saida)

    # 3. Finaliza a permanência
    permanencia.data_hora_saida = saida
    permanencia.valor_total = valor
    permanencia.status = 'FINALIZADO'
    permanencia.save()

    # 4. Libera a vaga
    vaga = permanencia.vaga
    vaga.status = 'LIVRE'
    vaga.save()

    return permanencia


def _calcular_valor(entrada, saida):
    """R$ 5,00 por hora; frações arredondadas para cima; mínimo de 1 hora."""
    minutos = int((saida - entrada).total_seconds() // 60)
    horas = max(1, math.ceil(minutos / 60))
    return TARIFA_POR_HORA * horas
