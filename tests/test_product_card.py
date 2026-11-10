import json
import unittest

from bipsystem.bipsystem import product_form_panel


class ProductCardRenderingTests(unittest.TestCase):
    def test_product_card_preserves_bindings_and_visual_contract(self) -> None:
        rendered = json.dumps(
            product_form_panel().render(),
            ensure_ascii=False,
        )

        for text in ("Dados", "Informe", "Tipo", "Marca", "Peso", "Barras"):
            self.assertIn(text, rendered)

        self.assertIn("product-form-card", rendered)
        self.assertIn("product-form-label", rendered)
        self.assertIn("product-form-input", rendered)
        self.assertIn("product-add-button", rendered)
        self.assertIn("Cadastrar Produto", rendered)
        self.assertIn("set_product_tipo", rendered)
        self.assertIn("set_product_marca", rendered)
        self.assertIn("set_product_peso", rendered)
        self.assertIn("set_product_codigo_de_barra", rendered)
        self.assertIn("register_product", rendered)
        self.assertEqual(rendered.count("product-form-input"), 4)


if __name__ == "__main__":
    unittest.main()
