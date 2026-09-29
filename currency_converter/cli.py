"""Interface de terminal do conversor: pergunta as moedas e o valor."""
from .converter import (
    SUPPORTED_CURRENCIES,
    CurrencyConverter,
    CurrencyError,
    RatesUnavailableError,
)


def run(input_fn=input, print_fn=print, converter=None, use_api=False):
    """Roda uma conversão. Devolve 0 se deu certo e 1 se deu erro.

    input_fn e print_fn são parâmetros pra eu conseguir simular o usuário
    digitando nos testes."""
    converter = converter or CurrencyConverter()
    if use_api:
        try:
            converter.fetch_rates()
        except RatesUnavailableError:
            print_fn("Aviso: API indisponível, usando taxas pré-definidas.")

    options = ", ".join(SUPPORTED_CURRENCIES)
    print_fn(f"Moedas disponíveis: {options}")
    try:
        src = input_fn("Moeda de origem: ")
        dst = input_fn("Moeda de destino: ")
        amount = input_fn("Quantidade: ")
        result = converter.convert(src, dst, amount)
    except CurrencyError as exc:
        print_fn(f"Erro: {exc}")
        return 1
    print_fn(f"{amount.strip()} {src.strip().upper()} = {result} {dst.strip().upper()}")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(run(use_api="--api" in sys.argv))
