"""Conversor de moedas (USD, EUR e BRL).

Usei Decimal em vez de float porque float dá uns erros bobos de
arredondamento (tipo 0.1 + 0.2 != 0.3), e com dinheiro isso não pode.
O arredondamento é half-up com 2 casas.

Exemplo:
    >>> conv = CurrencyConverter()
    >>> conv.convert("USD", "BRL", "10")
    Decimal('55.00')
"""
import json
import time
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from urllib.error import URLError
from urllib.request import urlopen

SUPPORTED_CURRENCIES = ("USD", "EUR", "BRL")

# Taxas fixas de reserva, sempre em relação a 1 USD.
# São valores de exemplo, não são cotação de verdade.
DEFAULT_RATES = {
    "USD": Decimal("1"),
    "EUR": Decimal("0.92"),
    "BRL": Decimal("5.50"),
}

API_URL = "https://open.er-api.com/v6/latest/USD"
TWO_PLACES = Decimal("0.01")


class CurrencyError(ValueError):
    """Erro geral do conversor (os outros herdam dele)."""


class UnsupportedCurrencyError(CurrencyError):
    """A moeda não está na lista (USD, EUR, BRL)."""


class InvalidAmountError(CurrencyError):
    """Valor que não dá pra converter: texto, negativo, NaN ou infinito."""


class RatesUnavailableError(CurrencyError):
    """Deu problema ao buscar as taxas na API."""


def parse_amount(value):
    """Transforma a entrada em Decimal e checa se é um valor aceitável.

    Aceita int, float, Decimal e str (com ponto ou vírgula). Zero pode,
    negativo não.
    """
    if isinstance(value, bool) or value is None:
        raise InvalidAmountError("Valor inválido.")
    if isinstance(value, str):
        value = value.strip().replace(",", ".")
    try:
        amount = Decimal(str(value))
    except InvalidOperation:
        raise InvalidAmountError(f"Valor não numérico: {value!r}") from None
    if not amount.is_finite():
        raise InvalidAmountError("Valor deve ser finito.")
    if amount < 0:
        raise InvalidAmountError("Valor não pode ser negativo.")
    return amount


class CurrencyConverter:
    """Faz a conversão entre as moedas suportadas.

    rates: dicionário {moeda: taxa por 1 USD}. Se não passar nada, usa
        DEFAULT_RATES.
    opener: função que abre a URL (igual ao urlopen). Deixei como parâmetro
        pra poder trocar por um mock nos testes e não depender de internet.
    """

    def __init__(self, rates=None, opener=urlopen):
        self.rates = dict(rates or DEFAULT_RATES)
        self._opener = opener
        self.updated_at = None  # quando a API atualizou as taxas pela última vez (Unix)

    @staticmethod
    def _normalize(code):
        code = str(code).strip().upper()
        if code not in SUPPORTED_CURRENCIES:
            raise UnsupportedCurrencyError(
                f"Moeda não suportada: {code!r}. Use: {', '.join(SUPPORTED_CURRENCIES)}."
            )
        return code

    def convert(self, from_currency, to_currency, amount):
        """Converte e devolve um Decimal com 2 casas (arredondando half-up).

        A conta é: valor / taxa da origem * taxa do destino. Como as taxas
        são todas em relação ao dólar, isso funciona pra qualquer par.
        """
        src = self._normalize(from_currency)
        dst = self._normalize(to_currency)
        value = parse_amount(amount)
        result = value / self.rates[src] * self.rates[dst]
        return result.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    def fetch_rates(self):
        """Busca as taxas na API. Se algo falhar, levanta RatesUnavailableError
        e mantém as taxas que já tinha."""
        try:
            with self._opener(API_URL, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if data.get("result") != "success":
                raise RatesUnavailableError("API retornou resposta sem sucesso.")
            new_rates = {c: Decimal(str(data["rates"][c])) for c in SUPPORTED_CURRENCIES}
        except (URLError, OSError, ValueError, KeyError) as exc:
            if isinstance(exc, RatesUnavailableError):
                raise
            raise RatesUnavailableError(f"Falha ao acessar a API: {exc}") from exc
        self.rates = new_rates
        self.updated_at = data.get("time_last_update_unix", time.time())
        return dict(self.rates)

    def rates_are_fresh(self, max_age_seconds=86400, now=None):
        """Diz se as taxas vieram da API há menos de max_age_seconds (padrão: 24h).

        Se nunca buscou na API, devolve False."""
        if self.updated_at is None:
            return False
        now = time.time() if now is None else now
        return (now - self.updated_at) <= max_age_seconds
