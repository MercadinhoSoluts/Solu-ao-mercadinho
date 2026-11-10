import json
import unittest

from bipsystem.bipsystem import conference_form_panel


class ConferenceCardRenderingTests(unittest.TestCase):
    def test_conference_card_preserves_fields_and_visual_contract(self) -> None:
        rendered = json.dumps(
            conference_form_panel().render(),
            ensure_ascii=False,
        )

        self.assertIn("Dados da Confer", rendered)
        self.assertIn("Informe os dados para realizar a confer", rendered)
        self.assertIn("do Produto", rendered)
        self.assertIn("Quantidade de Produtos", rendered)
        self.assertIn("Data de Validade do Lote", rendered)
        self.assertIn("Digite o c", rendered)
        self.assertIn("Digite o n", rendered)
        self.assertIn("Digite a quantidade em unidades", rendered)
        self.assertIn("dd/mm/aaaa", rendered)
        self.assertIn("conference-form-card", rendered)
        self.assertIn("conference-form-input", rendered)
        self.assertIn("conference-date-input", rendered)
        self.assertIn("conference-add-button", rendered)
        self.assertIn("type:\\\"date\\\"", rendered)
        self.assertIn("onChange", rendered)
        self.assertEqual(rendered.count("registration-form-input conference-form-input"), 4)


if __name__ == "__main__":
    unittest.main()
