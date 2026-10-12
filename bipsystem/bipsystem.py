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
            "background": "#307CE8",
        },
        "input": {
            "color": "white",
        },
        "input::placeholder": {
            "color": "rgba(255, 255, 255, 0.82) !important",
            "opacity": "1 !important",
        },
        ".rt-TextFieldRoot:focus-within": {
            "outline": "none !important",
            "border": "none !important",
            "box_shadow": "none !important",
            "background": "transparent !important",
        },
        "img": {
            "display": "block",
            "max_width": "100%",
        },
    },
)
app.add_page(login_page, route="/")