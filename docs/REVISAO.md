# Revisão de código e documentação

## O que conferi

- Os 27 testes passam (`python -m unittest`).
- Cada critério de aceitação (CA1 a CA5) tem testes ligados a ele; a tabela está na documentação técnica.
- Testei casos positivos e negativos: moeda inválida, valor negativo, texto, NaN e API fora do ar.
- O código usa `Decimal` no lugar de `float` pra não ter erro de arredondamento.
- A API é testada com mock, então os testes rodam sem internet.

## Melhorias que eu sugiro

1. As taxas de reserva são valores de exemplo. Dá pra atualizar ou ler de um arquivo de configuração.
2. Guardar em disco (cache) as taxas da API, pra não fazer uma chamada toda vez que o programa abrir.
3. Só existem USD, EUR e BRL. A lista de moedas poderia ser configurável.
4. Se o usuário digita algo errado, o programa encerra. Seria melhor perguntar de novo.
5. A interface é só no terminal. O enunciado pede "amigável", e uma interface gráfica ou web atenderia melhor.
6. Colocar GitHub Actions pra rodar os testes a cada push.
7. Medir a cobertura dos testes (`coverage.py`) e definir uma meta.
8. Os testes usam mock da API. Faltou um teste de integração com a API de verdade, separado dos outros.
9. Na documentação, faltam exemplos de uso do conversor como biblioteca (fora do terminal).
