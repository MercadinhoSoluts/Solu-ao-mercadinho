import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_xano_export import validate_export


class XanoExportValidationTests(unittest.TestCase):
    def write_export(self, directory: Path, name: str, records: list[dict]) -> None:
        (directory / name).write_text(json.dumps(records), encoding="utf-8")

    def valid_export(self, directory: Path) -> None:
        self.write_export(
            directory,
            "users.json",
            [
                {
                    "id": 1,
                    "email": "employee@example.invalid",
                    "role": "caixa",
                    "password": "not-exported-in-report",
                },
                {
                    "id": 2,
                    "email": "manager@example.invalid",
                    "role": "admin",
                },
                {
                    "id": 3,
                    "email": "owner@example.invalid",
                    "role": "proprietario",
                },
            ],
        )
        self.write_export(
            directory,
            "produtos.json",
            [{"id": 11, "nome": "Leite", "marca": "Marca", "peso": 1000}],
        )
        self.write_export(
            directory,
            "codigobarra.json",
            [{"id": 21, "produtos_id": 11, "codigo_de_barras": "7890001"}],
        )
        self.write_export(
            directory,
            "estoque.json",
            [
                {
                    "id": 31,
                    "produtos_id": 11,
                    "lote": 1,
                    "unidades": 3,
                    "validade": "2027-01-31",
                },
                {
                    "id": 32,
                    "produtos_id": 11,
                    "lote": 2,
                    "unidades": 4,
                    "validade": "2027-01-31",
                },
            ],
        )
        self.write_export(
            directory,
            "preco.json",
            [
                {
                    "id": 41,
                    "produtos_id": 11,
                    "preco_unitario": "12.50",
                    "created_at": "2026-10-01T12:30:00Z",
                }
            ],
        )

    def test_valid_export_reports_mapping_and_business_role_aliases(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            self.valid_export(directory)

            report = validate_export(directory)
            repeated_report = validate_export(directory)

        self.assertTrue(report["ready_for_manual_import"])
        self.assertEqual(
            report["role_counts"], {"manager": 1, "operator": 1, "owner": 1}
        )
        self.assertEqual(report["counts"]["stock_groups_after_merge"], 1)
        self.assertEqual(report["product_id_map"], repeated_report["product_id_map"])
        self.assertRegex(
            report["product_id_map"]["11"],
            r"^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$",
        )
        self.assertFalse(report["database_modified"])
        self.assertNotIn("not-exported-in-report", json.dumps(report))
        self.assertTrue(
            any("cannot be transferred" in warning for warning in report["warnings"])
        )
        self.assertTrue(
            any("multiple batch labels" in warning for warning in report["warnings"])
        )

    def test_export_with_duplicate_barcode_fails_validation(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            self.valid_export(directory)
            self.write_export(
                directory,
                "produtos.json",
                [
                    {"id": 11, "nome": "Leite", "marca": "Marca", "peso": 1000},
                    {"id": 12, "nome": "Suco", "marca": "Marca", "peso": 1000},
                ],
            )
            self.write_export(
                directory,
                "codigobarra.json",
                [
                    {"id": 21, "produtos_id": 11, "codigo_de_barras": "7890001"},
                    {"id": 22, "produtos_id": 12, "codigo_de_barras": "7890001"},
                ],
            )

            report = validate_export(directory)

        self.assertFalse(report["ready_for_manual_import"])
        self.assertTrue(any("belongs to multiple products" in error for error in report["errors"]))

    def test_missing_exports_are_reported_without_writing_to_database(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            report = validate_export(Path(temporary_directory))

        self.assertFalse(report["ready_for_manual_import"])
        self.assertEqual(len(report["errors"]), 5)
        self.assertFalse(report["database_modified"])


if __name__ == "__main__":
    unittest.main()
