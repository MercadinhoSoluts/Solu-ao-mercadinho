from typing import Any

import reflex as rx


class LoginState(rx.State):
    user: str = ""
    senha: str = ""
    feedback: str = ""

    def submit(self, form_data: dict[str, Any]) -> None:
        user = form_data.get("user", "").strip()
        senha = form_data.get("senha", "")
        self.user = user
        self.senha = senha

        if not user or not senha:
            self.feedback = "Preencha usuário e senha para continuar."
            return

        self.feedback = "Validação local concluída. A autenticação será adicionada posteriormente."


def field(
    icon_name: str,
    placeholder: str,
    name: str,
    input_type: str = "text",
) -> rx.Component:
    return rx.hstack(
        rx.icon(
            icon_name,
            size=20,
            stroke_width=1.5,
            color="white",
            aria_hidden="true",
        ),
        rx.input(
            name=name,
            type=input_type,
            placeholder=placeholder,
            aria_label=placeholder,
            variant="soft",
            color="white",
            background="transparent",
            border="none",
            box_shadow="none",
            font_size="1rem",
            flex="1",
            height="100%",
            padding="0",
            _placeholder={"color": "rgba(255, 255, 255, 0.82)"},
            _focus={
                "outline": "none",
                "border": "none",
                "box_shadow": "none",
                "background": "transparent",
            },
            _focus_visible={
                "outline": "none",
                "border": "none",
                "box_shadow": "none",
                "background": "transparent",
            },
        ),
        width="100%",
        height="2.9rem",
        padding="0 0.9rem",
        gap="0.8rem",
        align="center",
        border="1px solid rgba(255, 255, 255, 0.72)",
        border_radius="0.25rem",
        background="rgba(34, 111, 232, 0.18)",
        transition="background 160ms ease, border-color 160ms ease",
        _focus_within={
            "border_color": "white",
            "background": "rgba(34, 111, 232, 0.3)",
        },
    )


def login_page() -> rx.Component:
    return rx.box(
        rx.box(
            rx.box(
                position="absolute",
                width="clamp(18rem, 38vw, 34rem)",
                height="clamp(18rem, 38vw, 34rem)",
                border_radius="50%",
                background="#465FF5",
                left="clamp(-17rem, -18vw, -8rem)",
                bottom="clamp(-18rem, -20vw, -9rem)",
            ),
            rx.box(
                position="absolute",
                width="clamp(17rem, 34vw, 31rem)",
                height="clamp(17rem, 34vw, 31rem)",
                border_radius="50%",
                background="#244CC2",
                right="clamp(-16rem, -17vw, -8rem)",
                top="clamp(-16rem, -18vw, -8rem)",
            ),
            rx.box(
                position="absolute",
                width="clamp(9rem, 19vw, 16rem)",
                height="clamp(9rem, 19vw, 16rem)",
                border_radius="50%",
                background="#4D91F5",
                left="clamp(8%, 15vw, 19rem)",
                top="clamp(-5rem, -5vw, -2rem)",
                opacity="0.75",
            ),
            rx.box(
                position="absolute",
                width="clamp(8rem, 16vw, 14rem)",
                height="clamp(8rem, 16vw, 14rem)",
                border_radius="50%",
                background="#245FD1",
                right="clamp(8%, 15vw, 19rem)",
                bottom="clamp(-5rem, -5vw, -2rem)",
                opacity="0.85",
            ),
            rx.box(
                position="absolute",
                width="clamp(5rem, 10vw, 9rem)",
                height="clamp(5rem, 10vw, 9rem)",
                border_radius="50%",
                background="#2B7EFF",
                right="clamp(22%, 28vw, 34rem)",
                top="clamp(10%, 18vh, 9rem)",
                opacity="0.7",
            ),
            rx.box(
                position="absolute",
                width="clamp(4rem, 8vw, 7rem)",
                height="clamp(4rem, 8vw, 7rem)",
                border_radius="50%",
                background="#4D91F5",
                left="clamp(20%, 27vw, 33rem)",
                bottom="clamp(12%, 16vh, 8rem)",
                opacity="0.6",
            ),
            rx.box(
                position="absolute",
                width="clamp(6rem, 10vw, 9rem)",
                height="clamp(6rem, 10vw, 9rem)",
                border_radius="50%",
                background="#4D91F5",
                right="-2rem",
                top="42%",
                opacity="0.58",
            ),
            rx.box(
                position="absolute",
                width="clamp(4rem, 7vw, 6rem)",
                height="clamp(4rem, 7vw, 6rem)",
                border_radius="50%",
                background="#465FF5",
                left="-1.5rem",
                top="34%",
                opacity="0.72",
            ),
            rx.vstack(
                rx.vstack(
                    rx.heading(
                        "BIPSYSTEM",
                        font_size="54px",
                        color="white",
                        font_family="'Segoe Script', 'Brush Script MT', cursive",
                        font_weight="700",
                        letter_spacing="0.04em",
                        line_height="1",
                        text_align="center",
                    ),
                    rx.image(
                        src="/logo_bipsystem_branca.png",
                        alt="Logo BIPSYSTEM",
                        width="min(9rem, 42vw)",
                        height="auto",
                        object_fit="contain",
                        transform="translateY(-30px)",
                    ),
                    gap="65px",
                    align="center",
                    transform="translateY(-6px)",
                ),
                rx.form(
                    rx.vstack(
                        field("user-round", "Usuário", "user"),
                        field("lock-keyhole", "Senha", "senha", "password"),
                        rx.button(
                            "Login",
                            type="submit",
                            width="100%",
                            height="3.25rem",
                            margin_top="0.65rem",
                            border_radius="0.25rem",
                            background="white",
                            color="#2B7EFF",
                            font_size="24px",
                            font_weight="700",
                            box_shadow="0 8px 18px rgba(22, 74, 179, 0.16)",
                            transition="transform 160ms ease, box-shadow 160ms ease",
                            _hover={
                                "transform": "translateY(-1px)",
                                "box_shadow": "0 10px 22px rgba(22, 74, 179, 0.24)",
                            },
                            _focus_visible={
                                "outline": "3px solid rgba(255, 255, 255, 0.72)",
                                "outline_offset": "3px",
                            },
                            transform="translateY(20px)",
                        ),
                        rx.text(
                            LoginState.feedback,
                            role="status",
                            color="white",
                            font_size="0.82rem",
                            line_height="1.35",
                            text_align="center",
                            min_height="2.2rem",
                            padding_top="0.35rem",
                        ),
                        width="100%",
                        gap="0.85rem",
                    ),
                    on_submit=LoginState.submit,
                    reset_on_submit=False,
                    width="100%",
                    transform="translateY(40px)",
                ),
                position="relative",
                z_index="1",
                width="min(100%, 21rem)",
                gap="2.2rem",
                align="center",
            ),
            position="relative",
            overflow="hidden",
            width="100%",
            height="100%",
            min_height="100vh",
            padding="2rem 1.5rem 3rem",
            display="flex",
            align_items="center",
            justify_content="center",
            background="#307CE8",
            isolation="isolate",
        ),
        width="100%",
        height="100vh",
        min_height="100dvh",
        display="flex",
        align_items="center",
        justify_content="center",
        overflow="hidden",
        background="#307CE8",
    )


TEMPORARY_USER_NAME = "(nome)"

ROUTE_BY_DESTINATION = {
    "home": "/",
    "inventory": "/estoque",
    "receiving": "/conferencia",
    "products": "/produtos",
    "reports": "/relatorios",
    "registration": "/cadastro",
}

SIDEBAR_ITEMS = (
    ("Início", "home"),
    ("Estoque", "inventory"),
    ("Conferência", "receiving"),
    ("Produto", "products"),
    ("Relatórios", "reports"),
    ("Cadastro", "registration"),
)

DASHBOARD_CARDS = (
    {
        "title": "Estoque",
        "description": "Verifique o estoque dos produtos",
        "icon": "package",
        "color": "#3B82F6",
        "destination": "inventory",
    },
    {
        "title": "Conferência",
        "description": "Adicione os produtos recém chegados ao estoque",
        "icon": "database-zap",
        "color": "#22C55E",
        "destination": "receiving",
    },
    {
        "title": "Produto",
        "description": "Adicione um novo produto ao seu estoque",
        "icon": "shopping-bag",
        "color": "#F59E0B",
        "destination": "products",
    },
    {
        "title": "Relatórios",
        "description": "Acesse os relatórios das suas atividades",
        "icon": "chart-no-axes-column",
        "color": "#EC4899",
        "destination": "reports",
    },
    {
        "title": "Cadastro",
        "description": "Cadastre novos funcionários",
        "icon": "user-plus",
        "color": "#A3E635",
        "destination": "registration",
    },
)

REPORT_CARDS = (
    {
        "title": "Data próxima",
        "description": "Produtos com data de validade próxima",
        "icon": "calendar-clock",
        "color": "#FF0004",
    },
    {
        "title": "Estoque baixo",
        "description": "Produtos que estão com estoque baixo",
        "icon": "package-x",
        "color": "#FF0004",
    },
    {
        "title": "Vendas semanais",
        "description": "Relatório de vendas semanais",
        "icon": "trending-up",
        "color": "#77FF80",
    },
    {
        "title": "Vendas diárias",
        "description": "Relatório de vendas diárias",
        "icon": "trending-up",
        "color": "#77FF80",
    },
)

# Dados locais apenas para demonstrar a composição visual da tela de estoque.
DEMO_INVENTORY = (
    {
        "name": "Margarina Qualy c/sal (500g)",
        "batch": "12345",
        "quantity": "134",
        "barcode": "12345677",
        "expiration": "02/01/27",
    },
    {
        "name": "Margarina Qualy c/sal (250g)",
        "batch": "12345",
        "quantity": "134",
        "barcode": "12345678",
        "expiration": "02/01/27",
    },
    {
        "name": "Margarina Qualy s/sal (500g)",
        "batch": "12345",
        "quantity": "134",
        "barcode": "12345688",
        "expiration": "02/01/27",
    },
    {
        "name": "Margarina Qualy s/sal (250g)",
        "batch": "12345",
        "quantity": "134",
        "barcode": "12345679",
        "expiration": "02/01/27",
    },
)


def sidebar_item(label: str, destination: str, is_active: bool = False) -> rx.Component:
    return rx.vstack(
        rx.link(
            rx.button(
                rx.hstack(
                    rx.text(label),
                    rx.icon(
                        "chevron-right",
                        size=18,
                        color="white",
                        stroke_width=2,
                        aria_hidden="true",
                    ),
                    width="100%",
                    align="center",
                    justify="between",
                ),
                type="button",
                variant="ghost",
                width="100%",
                min_width="0",
                margin="0",
                box_sizing="border-box",
                padding="0.72rem 1.15rem",
                border_radius="0.35rem",
                color="white",
                font_size="0.98rem",
                font_weight="500",
                cursor="pointer",
                background="#2D66D9" if is_active else "transparent",
                box_shadow="inset 0 0 0 1px rgba(255, 255, 255, 0.12)" if is_active else "none",
                data_destination=destination,
                _hover={
                    "background": "#2D66D9" if is_active else "rgba(255, 255, 255, 0.16)",
                },
                _focus_visible={
                    "outline": "3px solid rgba(255, 255, 255, 0.88)",
                    "outline_offset": "2px",
                },
                _active={"background": "#255CC6" if is_active else "rgba(255, 255, 255, 0.24)"},
            ),
            href=ROUTE_BY_DESTINATION.get(destination, "/"),
            width="100%",
            display="block",
            text_decoration="none",
        ),
        rx.box(
            width="100%",
            height="1px",
            background="rgba(255, 255, 255, 0.38)",
        ),
        width="100%",
        gap="0",
    )


def sidebar(active_destination: str = "home") -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.button(
                rx.text(
                    "Nome",
                    font_size="1.2rem",
                    font_weight="700",
                    color="white",
                ),
                type="button",
                variant="ghost",
                width="100%",
                padding="0.65rem 0.75rem 0.9rem",
                border_radius="0.35rem",
                color="white",
                cursor="pointer",
                data_destination="profile",
                _hover={"background": "rgba(255, 255, 255, 0.16)"},
                _focus_visible={
                    "outline": "3px solid rgba(255, 255, 255, 0.88)",
                    "outline_offset": "2px",
                },
                _active={"background": "rgba(255, 255, 255, 0.24)"},
            ),
            rx.vstack(
                rx.box(
                    width="100%",
                    height="1px",
                    margin="0 0 0.35rem",
                    background="rgba(255, 255, 255, 0.55)",
                ),
                *[
                    sidebar_item(
                        label,
                        destination,
                        is_active=(destination == active_destination),
                    )
                    for label, destination in SIDEBAR_ITEMS
                ],
                width="100%",
                gap="0",
            ),
            width="100%",
            align="stretch",
        ),
        width="16rem",
        min_width="16rem",
        min_height="100dvh",
        padding="2.3rem 1.15rem",
        class_name="dashboard-sidebar",
        background="#3B82F6",
        color="white",
    )


def dashboard_header(subtitle: str = "Aqui está um resumo do seu mercado hoje.") -> rx.Component:
    return rx.vstack(
        rx.heading(
            f"Olá, {TEMPORARY_USER_NAME}",
            size="8",
            color="#172033",
            font_weight="700",
            line_height="1.15",
        ),
        rx.text(
            subtitle,
            color="#7A8496",
            font_size="1rem",
        ),
        align="start",
        gap="0.55rem",
        transform="translateX(-80px)",
    )


def dashboard_card(card: dict[str, str], destination: str | None = None) -> rx.Component:
    card_button = rx.button(
        rx.vstack(
            rx.box(
                rx.icon(card["icon"], size=26, color="white", stroke_width=2),
                display="flex",
                align_items="center",
                justify_content="center",
                width="3.5rem",
                height="3.5rem",
                border_radius="50%",
                background=card["color"],
            ),
            rx.text(
                card["title"],
                color="#172033",
                font_size="1.08rem",
                font_weight="700",
                text_align="center",
            ),
            rx.text(
                card["description"],
                color="#7A8496",
                font_size="0.91rem",
                line_height="1.45",
                text_align="center",
            ),
            align="center",
            justify="center",
            gap="0.85rem",
            width="100%",
        ),
        type="button",
        variant="ghost",
        width="100%",
        min_width="0",
        height="16rem",
        min_height="16rem",
        margin="0",
        box_sizing="border-box",
        padding="1.5rem 1.15rem",
        border_radius="0.7rem",
        background="white",
        box_shadow="0 5px 18px rgba(23, 32, 51, 0.08)",
        cursor="pointer",
        data_destination=destination or "report",
        transition="transform 160ms ease, box-shadow 160ms ease",
        _hover={
            "transform": "translateY(-3px)",
            "box_shadow": "0 9px 24px rgba(23, 32, 51, 0.14)",
        },
        _focus_visible={
            "outline": "3px solid #93C5FD",
            "outline_offset": "3px",
        },
        _active={"transform": "translateY(-1px)"},
    )

    if destination is None:
        return card_button

    return rx.link(
        card_button,
        href=ROUTE_BY_DESTINATION.get(destination, "/"),
        width="100%",
        display="block",
        text_decoration="none",
    )


def dashboard_cards() -> rx.Component:
    return rx.vstack(
        rx.box(
            *[
                dashboard_card(card, destination=card["destination"])
                for card in DASHBOARD_CARDS[:3]
            ],
            width="100%",
            max_width="62rem",
            display="grid",
            grid_template_columns="1fr",
            class_name="dashboard-card-grid dashboard-card-grid-primary",
            gap="2.5rem",
        ),
        rx.box(
            *[
                dashboard_card(card, destination=card["destination"])
                for card in DASHBOARD_CARDS[3:]
            ],
            width="100%",
            max_width="40.25rem",
            display="grid",
            grid_template_columns="1fr",
            class_name="dashboard-card-grid dashboard-card-grid-secondary",
            gap="5rem",
        ),
        width="100%",
        align="center",
        gap="2.5rem",
    )


def reports_cards() -> rx.Component:
    return rx.box(
        *[dashboard_card(card) for card in REPORT_CARDS],
        width="100%",
        max_width="62rem",
        display="grid",
        grid_template_columns="1fr",
        class_name="dashboard-card-grid dashboard-card-grid-reports",
        gap="2.5rem",
    )


def registration_form_panel() -> rx.Component:
    input_style = {
        "width": "100%",
        "height": "3.1rem",
        "padding": "0 1rem",
        "text_align": "center",
        "border_radius": "0.7rem",
        "border": "1px solid #E5E7EB",
        "background": "#D9D9D9",
        "color": "#000000",
        "box_shadow": "0 0 0 1px rgba(148, 163, 184, 0.08)",
        "font_size": "0.98rem",
        "_placeholder": {"color": "#000000", "opacity": "1", "text_align": "center"},
        "_focus": {
            "background": "#D9D9D9",
            "border_color": "#D9D9D9",
            "box_shadow": "0 0 0 2px rgba(217, 217, 217, 0.4)",
            "color": "#000000",
        },
        "_focus_visible": {
            "background": "#D9D9D9",
            "border_color": "#D9D9D9",
            "box_shadow": "0 0 0 2px rgba(217, 217, 217, 0.4)",
            "color": "#000000",
        },
        "_hover": {"background": "#D9D9D9"},
        "_active": {"background": "#D9D9D9"},
        "_selection": {"background": "rgba(0, 0, 0, 0.2)", "color": "#000000"},
    }

    return rx.box(
        rx.vstack(
            rx.vstack(
                rx.input(
                    type="text",
                    placeholder="Digite o nome do funcionário",
                    aria_label="Digite o nome do funcionário",
                    class_name="registration-form-input",
                    **input_style,
                ),
                rx.input(
                    type="email",
                    placeholder="Digite o e-mail do funcionário",
                    aria_label="Digite o e-mail do funcionário",
                    class_name="registration-form-input",
                    **input_style,
                ),
                rx.input(
                    type="password",
                    placeholder="Digite a senha desejada",
                    aria_label="Digite a senha desejada",
                    class_name="registration-form-input",
                    **input_style,
                ),
                rx.input(
                    type="text",
                    placeholder="Digite a função do funcionário",
                    aria_label="Digite a função do funcionário",
                    class_name="registration-form-input",
                    **input_style,
                ),
                rx.button(
                    "Cadastrar",
                    type="button",
                    width="100%",
                    height="3.2rem",
                    border_radius="0.7rem",
                    background="#3B82F6",
                    color="white",
                    font_size="0.98rem",
                    font_weight="700",
                    box_shadow="0 8px 18px rgba(59, 130, 246, 0.2)",
                    transition="transform 160ms ease, box-shadow 160ms ease, background 160ms ease",
                    _hover={
                        "transform": "translateY(-1px)",
                        "background": "#2563EB",
                        "box_shadow": "0 12px 22px rgba(37, 99, 235, 0.28)",
                    },
                    _focus_visible={
                        "outline": "3px solid rgba(147, 197, 253, 0.9)",
                        "outline_offset": "3px",
                    },
                    _active={"transform": "translateY(0)"},
                ),
                width="100%",
                gap="1rem",
                align="stretch",
            ),
            width="100%",
            max_width="42rem",
            gap="1.5rem",
            align="stretch",
        ),
        width="100%",
        max_width="42rem",
        margin="0 auto",
        background="white",
        border_radius="1rem",
        box_shadow="0 10px 28px rgba(23, 32, 51, 0.08)",
        padding="clamp(1.5rem, 3vw, 2.25rem)",
    )


def product_form_panel() -> rx.Component:
    input_style = {
        "width": "100%",
        "height": "3.1rem",
        "padding": "0 1rem",
        "text_align": "center",
        "border_radius": "0.7rem",
        "border": "1px solid #E5E7EB",
        "background": "#D9D9D9",
        "color": "#000000",
        "box_shadow": "0 0 0 1px rgba(148, 163, 184, 0.08)",
        "font_size": "0.98rem",
        "_placeholder": {"color": "#000000", "opacity": "1", "text_align": "center"},
        "_focus": {
            "background": "#D9D9D9",
            "border_color": "#D9D9D9",
            "box_shadow": "0 0 0 2px rgba(217, 217, 217, 0.4)",
            "color": "#000000",
        },
        "_focus_visible": {
            "background": "#D9D9D9",
            "border_color": "#D9D9D9",
            "box_shadow": "0 0 0 2px rgba(217, 217, 217, 0.4)",
            "color": "#000000",
        },
        "_hover": {"background": "#D9D9D9"},
        "_active": {"background": "#D9D9D9"},
        "_selection": {"background": "rgba(0, 0, 0, 0.2)", "color": "#000000"},
    }

    return rx.box(
        rx.vstack(
            rx.vstack(
                rx.input(
                    type="text",
                    placeholder="Digite o tipo do produto",
                    aria_label="Digite o tipo do produto",
                    class_name="registration-form-input",
                    **input_style,
                ),
                rx.input(
                    type="text",
                    placeholder="Digite a marca do produto",
                    aria_label="Digite a marca do produto",
                    class_name="registration-form-input",
                    **input_style,
                ),
                rx.input(
                    type="text",
                    placeholder="Digite o peso do produto",
                    aria_label="Digite o peso do produto",
                    class_name="registration-form-input",
                    **input_style,
                ),
                rx.input(
                    type="text",
                    placeholder="Digite o código de barra do produto",
                    aria_label="Digite o código de barra do produto",
                    class_name="registration-form-input",
                    **input_style,
                ),
                rx.button(
                    "Cadastrar",
                    type="button",
                    width="100%",
                    height="3.2rem",
                    border_radius="0.7rem",
                    background="#3B82F6",
                    color="white",
                    font_size="0.98rem",
                    font_weight="700",
                    box_shadow="0 8px 18px rgba(59, 130, 246, 0.2)",
                    transition="transform 160ms ease, box-shadow 160ms ease, background 160ms ease",
                    _hover={
                        "transform": "translateY(-1px)",
                        "background": "#2563EB",
                        "box_shadow": "0 12px 22px rgba(37, 99, 235, 0.28)",
                    },
                    _focus_visible={
                        "outline": "3px solid rgba(147, 197, 253, 0.9)",
                        "outline_offset": "3px",
                    },
                    _active={"transform": "translateY(0)"},
                ),
                width="100%",
                gap="1rem",
                align="stretch",
            ),
            width="100%",
            max_width="42rem",
            gap="1.5rem",
            align="stretch",
        ),
        width="100%",
        max_width="42rem",
        margin="0 auto",
        background="white",
        border_radius="1rem",
        box_shadow="0 10px 28px rgba(23, 32, 51, 0.08)",
        padding="clamp(1.5rem, 3vw, 2.25rem)",
    )


def conference_form_panel() -> rx.Component:
    input_style = {
        "width": "100%",
        "height": "3.1rem",
        "padding": "0 1rem",
        "text_align": "center",
        "border_radius": "0.7rem",
        "border": "1px solid #E5E7EB",
        "background": "#D9D9D9",
        "color": "#000000",
        "box_shadow": "0 0 0 1px rgba(148, 163, 184, 0.08)",
        "font_size": "0.98rem",
        "_placeholder": {"color": "#000000", "opacity": "1", "text_align": "center"},
        "_focus": {
            "background": "#D9D9D9",
            "border_color": "#D9D9D9",
            "box_shadow": "0 0 0 2px rgba(217, 217, 217, 0.4)",
            "color": "#000000",
        },
        "_focus_visible": {
            "background": "#D9D9D9",
            "border_color": "#D9D9D9",
            "box_shadow": "0 0 0 2px rgba(217, 217, 217, 0.4)",
            "color": "#000000",
        },
        "_hover": {"background": "#D9D9D9"},
        "_active": {"background": "#D9D9D9"},
        "_selection": {"background": "rgba(0, 0, 0, 0.2)", "color": "#000000"},
    }

    return rx.box(
        rx.vstack(
            rx.vstack(
                rx.input(
                    type="text",
                    placeholder="Código",
                    aria_label="Código",
                    class_name="registration-form-input",
                    **input_style,
                ),
                rx.input(
                    type="text",
                    placeholder="Lote",
                    aria_label="Lote",
                    class_name="registration-form-input",
                    **input_style,
                ),
                rx.input(
                    type="number",
                    placeholder="Unidades",
                    aria_label="Unidades",
                    class_name="registration-form-input",
                    **input_style,
                ),
                rx.input(
                    type="date",
                    placeholder="Validade",
                    aria_label="Validade",
                    class_name="registration-form-input conference-date-input",
                    min="0001-01-01",
                    max="9999-12-31",
                    **input_style,
                ),
                rx.button(
                    "Adicionar",
                    type="button",
                    width="100%",
                    height="3.2rem",
                    border_radius="0.7rem",
                    background="#3B82F6",
                    color="white",
                    font_size="0.98rem",
                    font_weight="700",
                    box_shadow="0 8px 18px rgba(59, 130, 246, 0.2)",
                    transition="transform 160ms ease, box-shadow 160ms ease, background 160ms ease",
                    _hover={
                        "transform": "translateY(-1px)",
                        "background": "#2563EB",
                        "box_shadow": "0 12px 22px rgba(37, 99, 235, 0.28)",
                    },
                    _focus_visible={
                        "outline": "3px solid rgba(147, 197, 253, 0.9)",
                        "outline_offset": "3px",
                    },
                    _active={"transform": "translateY(0)"},
                ),
                width="100%",
                gap="1rem",
                align="stretch",
            ),
            width="100%",
            max_width="42rem",
            gap="1.5rem",
            align="stretch",
        ),
        width="100%",
        max_width="42rem",
        margin="0 auto",
        background="white",
        border_radius="1rem",
        box_shadow="0 10px 28px rgba(23, 32, 51, 0.08)",
        padding="clamp(1.5rem, 3vw, 2.25rem)",
    )


def inventory_card(product: dict[str, str]) -> rx.Component:
    columns = (
        ("Nome", product["name"]),
        ("Lote", product["batch"]),
        ("Unid.", product["quantity"]),
        ("Cod.", product["barcode"]),
        ("Validade", product["expiration"]),
    )

    return rx.box(
        rx.box(
            *[
                rx.vstack(
                    rx.text(
                        heading,
                        color="#7A8496",
                        font_size="0.75rem",
                        font_weight="600",
                        line_height="1.2",
                    ),
                    rx.text(
                        value,
                        color="#172033",
                        font_size="0.92rem",
                        line_height="1.35",
                        white_space="normal" if heading == "Nome" else "nowrap",
                    ),
                    align="start",
                    gap="0.45rem",
                    min_width="0",
                    width="100%",
                )
                for heading, value in columns
            ],
            display="grid",
            grid_template_columns="minmax(15rem, 2.2fr) repeat(4, minmax(5.5rem, 1fr))",
            gap="1.25rem",
            min_width="41rem",
            width="100%",
        ),
        width="100%",
        overflow_x="auto",
        padding="1.1rem 1.25rem",
        background="white",
        border_radius="0.85rem",
        box_shadow="0 5px 18px rgba(23, 32, 51, 0.06)",
        box_sizing="border-box",
    )


def inventory_panel() -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.icon(
                "search",
                size=20,
                color="#000000",
                stroke_width=2,
                aria_hidden="true",
            ),
            rx.input(
                placeholder="Buscar produto...",
                aria_label="Buscar produto por nome, marca, peso, lote ou código de barras",
                type="text",
                class_name="inventory-search-input",
                width="100%",
                height="100%",
                padding="0",
                border="none",
                outline="none",
                background="transparent",
                color="#000000",
                font_size="0.95rem",
                _placeholder={"color": "#000000", "opacity": "1"},
                _focus={
                    "border": "none",
                    "outline": "none",
                    "box_shadow": "none",
                },
            ),
            width="100%",
            height="3.25rem",
            padding="0 1rem",
            gap="0.7rem",
            display="flex",
            flex_direction="row",
            align_items="center",
            background="white",
            border="1px solid #E5E7EB",
            border_radius="0.75rem",
            box_shadow="0 5px 18px rgba(23, 32, 51, 0.05)",
            transition="border-color 160ms ease, box-shadow 160ms ease",
            _focus_within={
                "border_color": "#93C5FD",
                "box_shadow": "0 0 0 3px rgba(147, 197, 253, 0.28)",
            },
        ),
        rx.box(
            *[inventory_card(product) for product in DEMO_INVENTORY],
            width="100%",
            display="flex",
            flex_direction="column",
            gap="0.85rem",
            overflow_y="auto",
            padding="0.15rem 0.35rem 0.5rem 0.15rem",
            max_height="calc(100dvh - 18rem)",
            min_height="12rem",
            scrollbar_width="thin",
        ),
        width="100%",
        max_width="62rem",
        margin="0 auto",
        gap="1.15rem",
        align="stretch",
    )


def dashboard_layout(
    content: rx.Component,
    active_destination: str = "home",
    subtitle: str = "Aqui está um resumo do seu mercado hoje.",
) -> rx.Component:
    return rx.hstack(
        sidebar(active_destination=active_destination),
        rx.box(
            rx.vstack(
                dashboard_header(subtitle=subtitle),
                content,
                width="100%",
                max_width="70rem",
                margin="0 auto",
                padding="clamp(2rem, 6vh, 4.5rem) clamp(1.25rem, 5vw, 5rem) 6rem",
                gap="clamp(3rem, 8vh, 5.5rem)",
                align="stretch",
            ),
            rx.image(
                src="/logo_bipsystem.png",
                alt="Logo BIPSYSTEM",
                width="7.5rem",
                height="auto",
                position="absolute",
                right="clamp(1.25rem, 4vw, 4rem)",
                bottom="1.5rem",
            ),
            position="relative",
            flex="1",
            min_width="0",
            min_height="100dvh",
            overflow="auto",
            background="#F7F9FC",
        ),
        width="100%",
        min_height="100dvh",
        align="stretch",
        gap="0",
        background="#F7F9FC",
    )


@rx.page(route="/")
def dashboard() -> rx.Component:
    return dashboard_layout(
        dashboard_cards(),
        active_destination="home",
        subtitle="Aqui está um resumo do seu mercado hoje.",
    )


@rx.page(route="/cadastro")
def registration_page() -> rx.Component:
    return dashboard_layout(
        registration_form_panel(),
        active_destination="registration",
        subtitle="Aqui você pode adicionar funcionários novos ao sistema de gerenciamento do mercado",
    )


@rx.page(route="/estoque")
def estoque_page() -> rx.Component:
    return dashboard_layout(
        inventory_panel(),
        active_destination="inventory",
        subtitle="Aqui está o estoque do mercado",
    )


@rx.page(route="/conferencia")
def conferencia_page() -> rx.Component:
    return dashboard_layout(
        conference_form_panel(),
        active_destination="receiving",
        subtitle="Aqui você pode adicionar produtos recém entregues pelo fornecedor ao seu estoque",
    )


@rx.page(route="/produtos")
def produtos_page() -> rx.Component:
    return dashboard_layout(
        product_form_panel(),
        active_destination="products",
        subtitle="Aqui você pode registrar produtos novos ao sistema do mercado",
    )


@rx.page(route="/relatorios")
def relatorios_page() -> rx.Component:
    return dashboard_layout(
        reports_cards(),
        active_destination="reports",
        subtitle="Aqui você pode acessar seus dashboards",
    )


app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=False,
        radius="small",
    ),
    style={
        "html, body, #root": {
            "width": "100%",
            "height": "100%",
            "min_width": "100%",
            "min_height": "100%",
            "margin": "0",
            "padding": "0",
            "overflow": "hidden",
        },
        "body": {
            "background": "#F7F9FC",
        },
        "input": {
            "color": "white",
        },
        "input::placeholder": {
            "color": "rgba(255, 255, 255, 0.82) !important",
            "opacity": "1 !important",
        },
        ".inventory-search-input, .inventory-search-input:focus, .inventory-search-input input, .inventory-search-input input:focus": {
            "color": "#000000 !important",
        },
        ".inventory-search-input::placeholder, .inventory-search-input input::placeholder": {
            "color": "#000000 !important",
            "opacity": "1 !important",
        },
        ".registration-form-input input": {
            "color": "#000000 !important",
        },
        ".registration-form-input input::placeholder": {
            "color": "#000000 !important",
            "opacity": "1 !important",
        },
        ".rt-TextFieldRoot:focus-within": {
            "outline": "none !important",
            "border": "none !important",
            "box_shadow": "none !important",
            "background": "transparent !important",
        },
        ".registration-form-input, .registration-form-input:focus-within": {
            "background": "#D9D9D9 !important",
        },
        ".registration-form-input input, .registration-form-input input:focus": {
            "background": "#D9D9D9 !important",
        },
        ".conference-date-input input": {
            "text_align": "center !important",
            "text_align_last": "center !important",
        },
        ".conference-date-input::-webkit-datetime-edit, .conference-date-input input::-webkit-datetime-edit, .conference-date-input::-webkit-date-and-time-value, .conference-date-input input::-webkit-date-and-time-value": {
            "display": "flex",
            "justify_content": "center",
            "align_items": "center",
            "text_align": "center !important",
            "padding": "0",
            "width": "100%",
            "margin": "0 auto",
            "box_sizing": "border-box",
        },
        ".conference-date-input::-webkit-datetime-edit-fields-wrapper, .conference-date-input input::-webkit-datetime-edit-fields-wrapper": {
            "display": "flex",
            "justify_content": "center",
            "align_items": "center",
            "width": "100%",
            "margin": "0 auto",
        },
        ".conference-date-input::-webkit-datetime-edit-text, .conference-date-input input::-webkit-datetime-edit-text, .conference-date-input::-webkit-datetime-edit-month-field, .conference-date-input input::-webkit-datetime-edit-month-field, .conference-date-input::-webkit-datetime-edit-day-field, .conference-date-input input::-webkit-datetime-edit-day-field, .conference-date-input::-webkit-datetime-edit-year-field, .conference-date-input input::-webkit-datetime-edit-year-field": {
            "text_align": "center",
        },
        ".dashboard-card-grid": {
            "grid_template_columns": "1fr",
        },
        "@media (min-width: 640px)": {
            ".dashboard-card-grid": {
                "grid_template_columns": "repeat(2, minmax(0, 1fr))",
            },
        },
        "@media (min-width: 1080px)": {
            ".dashboard-card-grid-primary": {
                "grid_template_columns": "repeat(3, minmax(0, 1fr))",
            },
        },
        "@media (max-width: 639px)": {
            ".dashboard-sidebar": {
                "width": "5.5rem",
                "min_width": "5.5rem",
                "padding": "1rem 0.35rem",
            },
            ".dashboard-sidebar img": {
                "width": "4.5rem",
                "margin_bottom": "0.8rem",
            },
            ".dashboard-sidebar button": {
                "justify_content": "center",
                "padding": "0.55rem 0.2rem",
                "font_size": "0.68rem",
                "line_height": "1.15",
                "text_align": "center",
                "white_space": "normal",
            },
        },
        "img": {
            "display": "block",
            "max_width": "100%",
        },
    },
)