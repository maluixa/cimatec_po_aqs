# Agile Docs & Code: Conversor de Moedas

Atividade que simula uma sprint Scrum: documentação, código e testes unitários de um conversor de moedas (USD, EUR e BRL).

Quadro Trello: (https://trello.com/invite/b/6abb0eaf3bdc6b04f157c33e/ATTIee155434fd9bcd8e3b39aa63930236543DAF5592/agile-docs-code-sprint)

## Estrutura

```
currency_converter/   código (converter.py e cli.py)
tests/                testes unitários (unittest)
docs/                 documentação, quadro Trello, revisão e imagens (docs/img)
```

## Como usar

```bash
python -m currency_converter.cli          # com as taxas fixas
python -m currency_converter.cli --api    # com taxas da API (se falhar, usa as fixas)
python -m unittest -v                     # rodar os testes
```

Precisa só do Python 3.8 ou mais novo, sem instalar nada.

## Documentos

- [Documentação técnica](docs/DOCUMENTACAO_TECNICA.md)
- [Revisão e melhorias](docs/REVISAO.md)
