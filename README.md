# Sistema de Estacionamento — Backend Django + Frontend

Backend reescrito em **Python + Django** (SQLite), substituindo o backend
original em Java 8 puro. Mantém os mesmos endpoints REST e as mesmas regras
de negócio. O frontend (HTML/CSS/JS) está incluído aqui também, sem nenhuma
alteração em relação ao original.

## Estrutura do projeto

```
estacionamento-django/
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml       # sobe backend + frontend juntos
├── frontend/                # cópia do frontend (HTML/CSS/JS + Nginx), sem alterações
├── estacionamento/          # projeto Django (settings, urls, middleware CORS)
└── api/                     # app Django
    ├── models.py            # Cliente, Veiculo, Vaga, Permanencia
    ├── urls.py
    ├── migrations/
    ├── views/                # uma view por recurso, retorna JsonResponse
    └── services/
        └── permanencia_service.py   # regras de negócio (entrada/saída/cálculo)
```

> O frontend aqui dentro é uma cópia do original em `aula-projeto-legado/frontend`.

## Como rodar (recomendado — via Docker)

Tudo roda a partir desta própria pasta — não precisa entrar em nenhuma outra:

```bash
cd estacionamento-django
docker compose up --build -d
```

Isso builda e inicia dois containers:

| Serviço  | Container                 | Porta local |
|----------|----------------------------|-------------|
| backend  | estacionamento-backend     | 8080        |
| frontend | estacionamento-frontend    | 3000        |

- Frontend: **http://localhost:3000**
- API: **http://localhost:8080/api/**

O `CMD` do Dockerfile já roda `python manage.py migrate` automaticamente
antes de iniciar o servidor, então o banco SQLite é criado/atualizado sem
nenhum passo manual. Os dados ficam no volume `sqlite_data`, então
persistem entre reinicializações (`docker compose restart` /
`docker compose down` + `up`, desde que o volume não seja removido).

Comandos úteis:

```bash
docker logs estacionamento-backend     # ver logs do backend
docker compose restart                 # reiniciar sem perder dados
docker compose down                    # parar (mantém o volume)
docker compose down -v                 # parar e apagar o banco (reseta tudo)
```

> ⚠️ A porta 8080 precisa estar livre na máquina. Se outro serviço já estiver
> usando essa porta, pare-o antes (`docker stop <container>`) ou altere o
> mapeamento de porta no `docker-compose.yml`.

## Como rodar localmente (sem Docker)

Útil para debugar o backend isoladamente.

```bash
cd estacionamento-django
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8080
```

A API fica em `http://localhost:8080/api/`.

Para usar o frontend servido fora do Docker apontando para esse backend
local, edite `frontend/js/api.js` e defina `API_BASE = 'http://localhost:8080'`
no topo do arquivo (ver detalhes em `contexto.txt`, seção "Frontend apontando
para o backend local").

## Endpoints da API

| Método        | URL                              | Descrição                         |
|----------------|-----------------------------------|------------------------------------|
| GET / POST     | `/api/clientes/`                  | Listar / cadastrar clientes        |
| GET/PUT/DELETE | `/api/clientes/<id>/`             | Detalhe / editar / excluir cliente |
| GET / POST     | `/api/veiculos/`                  | Listar / cadastrar veículos        |
| GET/PUT/DELETE | `/api/veiculos/<id>/`             | Detalhe / editar / excluir veículo |
| GET / POST     | `/api/vagas/`                      | Listar / cadastrar vagas (`?status=LIVRE`) |
| GET/PUT/DELETE | `/api/vagas/<id>/`                | Detalhe / editar / excluir vaga    |
| POST           | `/api/permanencias/entrada/`      | Registrar entrada (veiculoId, vagaId) |
| PUT            | `/api/permanencias/<id>/saida/`   | Registrar saída e calcular valor   |
| GET            | `/api/permanencias/`               | Listar permanências (`?status=ABERTO/FINALIZADO`) |
| GET            | `/api/dashboard/`                   | Totais: vagas livres/ocupadas, veículos estacionados |

As rotas aceitam com ou sem barra final (o frontend chama sem barra).

## Regras de negócio

- Cobrança: **R$ 5,00 por hora**, mínimo de 1 hora, fração arredondada para
  cima (`math.ceil`). Cálculo feito com `Decimal`, nunca `float`.
- Não é possível dar entrada em um veículo que já tem permanência aberta
  nem ocupar uma vaga já `OCUPADA` → retorna **409**.
- CPF, placa e número de vaga duplicados → **409**.
- Recurso inexistente (cliente, veículo, vaga, permanência) → **404**.
- Entrada/saída executadas dentro de uma transação (`transaction.atomic`),
  garantindo que o status da vaga e da permanência mudem juntos.

## Testando rapidamente (sem abrir o navegador)

```bash
curl http://localhost:8080/api/dashboard/
curl -X POST http://localhost:8080/api/clientes/ \
  -H "Content-Type: application/json" \
  -d '{"nome":"Teste","cpf":"123.456.789-00"}'
```

## Resetar o banco

Para garantir que o banco esteja limpo (sem clientes/veículos de teste, só
as 15 vagas iniciais A01–A10 e B01–B05):

```bash
docker exec estacionamento-backend python manage.py shell -c "
from api.models import Cliente, Veiculo, Permanencia, Vaga
Permanencia.objects.all().delete()
Veiculo.objects.all().delete()
Cliente.objects.all().delete()
Vaga.objects.update(status='LIVRE')
"
```
