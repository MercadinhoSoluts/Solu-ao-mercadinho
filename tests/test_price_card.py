import json
import unittest

from bipsystem.bipsystem import prices_panel


class PriceCardRenderingTests(unittest.TestCase):
    def test_price_card_preserves_functional_controls_and_visual_contract(self) -> None:
        rendered = json.dumps(
            prices_panel().render(),
            ensure_ascii=False,
            default=str,
        )

        self.assertIn("Cadastrar Pre", rendered)
        self.assertIn("Relacione um c", rendered)
        self.assertIn("barras", rendered)
        self.assertIn("Digite o c", rendered)
        self.assertIn("Pre", rendered)
        self.assertIn("R$ 0,00", rendered)
        self.assertIn("Vincular Pre", rendered)
        self.assertIn("Produto Selecionado", rendered)
        self.assertIn("prices-form-card", rendered)
        self.assertIn("prices-fields-grid", rendered)
        self.assertIn("prices-selected-details", rendered)


if __name__ == "__main__":
    unittest.main()
