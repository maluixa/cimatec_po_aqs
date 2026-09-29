"""Testes do conversor. Separei por critério de aceitação (CA1 a CA5),
mais os testes da API e da interface."""
import json
import unittest
from decimal import Decimal
from unittest.mock import MagicMock
from urllib.error import URLError

from currency_converter import cli
from currency_converter.converter import (
    CurrencyConverter,
    InvalidAmountError,
    RatesUnavailableError,
    UnsupportedCurrencyError,
)

RATES = {"USD": Decimal("1"), "EUR": Decimal("0.90"), "BRL": Decimal("5.00")}


def fake_response(payload):
    resp = MagicMock()
    resp.read.return_value = json.dumps(payload).encode()
    resp.__enter__.return_value = resp
    return resp


class TestCA1SelecionarMoedas(unittest.TestCase):
    def setUp(self):
        self.conv = CurrencyConverter(rates=RATES)

    def test_todas_as_combinacoes_suportadas(self):
        for a in ("USD", "EUR", "BRL"):
            for b in ("USD", "EUR", "BRL"):
                self.assertIsInstance(self.conv.convert(a, b, 1), Decimal)

    def test_codigo_minusculo_e_com_espacos(self):
        self.assertEqual(self.conv.convert(" usd ", "brl", 1), Decimal("5.00"))

    def test_moeda_origem_invalida(self):
        with self.assertRaises(UnsupportedCurrencyError):
            self.conv.convert("XYZ", "USD", 1)

    def test_moeda_destino_invalida(self):
        with self.assertRaises(UnsupportedCurrencyError):
            self.conv.convert("USD", "JPY", 1)


class TestCA2CA3QuantidadeEValorEquivalente(unittest.TestCase):
    def setUp(self):
        self.conv = CurrencyConverter(rates=RATES)

    def test_usd_para_brl(self):
        self.assertEqual(self.conv.convert("USD", "BRL", 10), Decimal("50.00"))

    def test_brl_para_eur(self):
        self.assertEqual(self.conv.convert("BRL", "EUR", 100), Decimal("18.00"))

    def test_mesma_moeda_retorna_o_mesmo_valor(self):
        self.assertEqual(self.conv.convert("EUR", "EUR", "12.34"), Decimal("12.34"))

    def test_zero(self):
        self.assertEqual(self.conv.convert("USD", "BRL", 0), Decimal("0.00"))

    def test_virgula_como_separador_decimal(self):
        self.assertEqual(self.conv.convert("USD", "BRL", "1,5"), Decimal("7.50"))

    def test_valor_negativo_e_rejeitado(self):
        with self.assertRaises(InvalidAmountError):
            self.conv.convert("USD", "BRL", -1)

    def test_valor_nao_numerico_e_rejeitado(self):
        for bad in ("abc", "", None, True, "nan", "inf"):
            with self.subTest(bad=bad), self.assertRaises(InvalidAmountError):
                self.conv.convert("USD", "BRL", bad)


class TestCA4CA5PrecisaoEArredondamento(unittest.TestCase):
    def test_duas_casas_decimais(self):
        conv = CurrencyConverter(rates=RATES)
        self.assertEqual(conv.convert("USD", "EUR", "3"), Decimal("2.70"))
        self.assertEqual(conv.convert("USD", "EUR", "3").as_tuple().exponent, -2)

    def test_arredonda_para_cima_na_metade(self):
        conv = CurrencyConverter(rates={"USD": Decimal("1"), "EUR": Decimal("0.5"), "BRL": Decimal("1")})
        # 0.01 * 0.5 = 0.005, que tem que arredondar pra 0.01
        self.assertEqual(conv.convert("USD", "EUR", "0.01"), Decimal("0.01"))

    def test_arredonda_para_baixo_abaixo_da_metade(self):
        conv = CurrencyConverter(rates={"USD": Decimal("1"), "EUR": Decimal("0.334"), "BRL": Decimal("1")})
        self.assertEqual(conv.convert("USD", "EUR", "1"), Decimal("0.33"))

    def test_sem_erro_de_ponto_flutuante(self):
        conv = CurrencyConverter(rates={"USD": Decimal("1"), "EUR": Decimal("1"), "BRL": Decimal("1.1")})
        self.assertEqual(conv.convert("USD", "BRL", "0.1"), Decimal("0.11"))

    def test_valores_grandes(self):
        conv = CurrencyConverter(rates=RATES)
        self.assertEqual(conv.convert("USD", "BRL", "1000000000"), Decimal("5000000000.00"))


class TestAPIeTaxas(unittest.TestCase):
    PAYLOAD = {
        "result": "success",
        "time_last_update_unix": 1_000_000,
        "rates": {"USD": 1, "EUR": 0.85, "BRL": 5.2, "JPY": 150},
    }

    def test_api_atualiza_taxas(self):
        opener = MagicMock(return_value=fake_response(self.PAYLOAD))
        conv = CurrencyConverter(opener=opener)
        conv.fetch_rates()
        opener.assert_called_once()
        self.assertEqual(conv.convert("USD", "BRL", 10), Decimal("52.00"))

    def test_api_indisponivel(self):
        conv = CurrencyConverter(opener=MagicMock(side_effect=URLError("sem rede")))
        with self.assertRaises(RatesUnavailableError):
            conv.fetch_rates()

    def test_api_resposta_sem_sucesso(self):
        opener = MagicMock(return_value=fake_response({"result": "error"}))
        with self.assertRaises(RatesUnavailableError):
            CurrencyConverter(opener=opener).fetch_rates()

    def test_api_json_sem_moeda_esperada(self):
        payload = {"result": "success", "rates": {"USD": 1}}
        opener = MagicMock(return_value=fake_response(payload))
        with self.assertRaises(RatesUnavailableError):
            CurrencyConverter(opener=opener).fetch_rates()

    def test_falha_da_api_preserva_taxas_anteriores(self):
        conv = CurrencyConverter(rates=RATES, opener=MagicMock(side_effect=URLError("x")))
        with self.assertRaises(RatesUnavailableError):
            conv.fetch_rates()
        self.assertEqual(conv.rates["BRL"], Decimal("5.00"))

    def test_taxas_atualizadas(self):
        conv = CurrencyConverter(opener=MagicMock(return_value=fake_response(self.PAYLOAD)))
        self.assertFalse(conv.rates_are_fresh())  # ainda não buscou na API
        conv.fetch_rates()
        self.assertTrue(conv.rates_are_fresh(now=1_000_000 + 3600))
        self.assertFalse(conv.rates_are_fresh(now=1_000_000 + 2 * 86400))


class TestInterface(unittest.TestCase):
    def _run(self, inputs, **kw):
        it = iter(inputs)
        out = []
        code = cli.run(
            input_fn=lambda _: next(it),
            print_fn=out.append,
            converter=CurrencyConverter(rates=RATES),
            **kw,
        )
        return code, out

    def test_fluxo_feliz(self):
        code, out = self._run(["usd", "brl", "10"])
        self.assertEqual(code, 0)
        self.assertEqual(out[-1], "10 USD = 50.00 BRL")

    def test_lista_moedas_disponiveis(self):
        _, out = self._run(["usd", "brl", "1"])
        self.assertIn("USD", out[0])

    def test_moeda_invalida_mostra_erro(self):
        code, out = self._run(["xxx", "brl", "10"])
        self.assertEqual(code, 1)
        self.assertTrue(out[-1].startswith("Erro:"))

    def test_valor_invalido_mostra_erro(self):
        code, out = self._run(["usd", "brl", "abc"])
        self.assertEqual(code, 1)
        self.assertTrue(out[-1].startswith("Erro:"))

    def test_api_offline_usa_taxas_predefinidas(self):
        it = iter(["usd", "brl", "1"])
        out = []
        conv = CurrencyConverter(rates=RATES, opener=MagicMock(side_effect=URLError("x")))
        code = cli.run(lambda _: next(it), out.append, conv, use_api=True)
        self.assertEqual(code, 0)
        self.assertTrue(out[0].startswith("Aviso"))


if __name__ == "__main__":
    unittest.main()
