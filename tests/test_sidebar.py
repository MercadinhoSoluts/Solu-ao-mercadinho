import json
import unittest

from bipsystem.bipsystem import (
    ROUTE_BY_DESTINATION,
    SIDEBAR_ITEMS,
    dashboard,
    sidebar,
)


class SidebarRenderingTests(unittest.TestCase):
    def test_sidebar_uses_brand_profile_navigation_and_logout(self) -> None:
        rendered = json.dumps(
            sidebar(active_destination="inventory").render(),
            ensure_ascii=False,
        )

        self.assertIn("BIPSYSTEM", rendered)
        self.assertNotIn("/logo_bipsystem_branca.png", rendered)
        self.assertIn("Segoe Script", rendered)
        self.assertIn("linear-gradient", rendered)
        self.assertIn("sidebar-wave-one", rendered)
        self.assertIn("sidebar-wave-two", rendered)
        self.assertIn("sidebar-wave-three", rendered)
        self.assertIn("19rem", rendered)
        self.assertIn("dashboard-sidebar", rendered)
        self.assertIn("sidebar-keyboard-capture", rendered)
        self.assertIn('direction:\\"row\\"', rendered)
        self.assertIn('direction:\\"column\\"', rendered)
        self.assertIn('justify:\\"center\\"', rendered)
        self.assertIn("Sair", rendered)
        self.assertIn("LucideUsers", rendered)
        self.assertIn("inventory", rendered)
        self.assertIn("active", rendered)

        for label, destination in SIDEBAR_ITEMS:
            serialized_label = json.dumps(label, ensure_ascii=True)[1:-1]
            serialized_label = serialized_label.replace("\\", "\\\\")
            self.assertIn(serialized_label, rendered)
            self.assertIn(ROUTE_BY_DESTINATION[destination], rendered)

    def test_dashboard_exposes_mobile_menu_and_shared_content_offset(self) -> None:
        rendered = json.dumps(dashboard().render(), ensure_ascii=False)

        self.assertIn("sidebar-menu-trigger", rendered)
        self.assertIn("dashboard-main", rendered)
        self.assertIn("onClick", rendered)


if __name__ == "__main__":
    unittest.main()
