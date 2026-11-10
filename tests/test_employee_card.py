import json
import unittest

from bipsystem.bipsystem import registration_form_panel


class EmployeeCardRenderingTests(unittest.TestCase):
    def test_employee_card_preserves_fields_options_and_visual_contract(self) -> None:
        rendered = json.dumps(
            registration_form_panel().render(),
            ensure_ascii=False,
        )

        self.assertIn("Dados do Funcion", rendered)
        self.assertIn("Informe os dados para cadastrar um novo funcion", rendered)
        self.assertIn("Nome do Funcion", rendered)
        self.assertIn("E-mail do Funcion", rendered)
        self.assertIn("Fun", rendered)
        self.assertIn("Digite o nome do funcion", rendered)
        self.assertIn("Digite o e-mail do funcion", rendered)
        self.assertIn("Digite a senha desejada", rendered)
        self.assertIn("Selecione a fun", rendered)
        self.assertIn("employee-form-card", rendered)
        self.assertIn("[\\\"maxWidth\\\"] : \\\"none\\\"", rendered)
        self.assertIn("employee-form-label", rendered)
        self.assertEqual(rendered.count("registration-form-input employee-form-input"), 4)
        self.assertIn("type:\\\"password\\\"", rendered)
        self.assertIn("Propriet", rendered)
        self.assertIn("Operador", rendered)
        self.assertIn("Admin", rendered)
        self.assertIn("onSubmit", rendered)


if __name__ == "__main__":
    unittest.main()
