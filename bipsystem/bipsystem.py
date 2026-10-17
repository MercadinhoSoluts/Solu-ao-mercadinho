import asyncio
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import reflex as rx

from bipsystem.auth_client import (
    XanoApiError,
    create_inventory_lot,
    create_product,
    create_employee,
    delete_employee,
    get_current_user,
    list_employees,
    list_inventory,
    list_products,
    is_valid_product_text,
    login,
    normalize_role,
    parse_inventory_date,
    parse_inventory_units,
    parse_product_weight,
    update_inventory_lot,
    validate_password,
    update_employee,
)

INVENTORY_OPERATION_LOCK = asyncio.Lock()


def find_inventory_record(
    inventory: list[dict[str, Any]],
    product_id: int,
    validity: str,
) -> dict[str, Any] | None:
    return next(
        (
            record
            for record in inventory
            if record.get("produtos_id") == product_id
            and str(record.get("validade") or "") == validity
        ),
        None,
    )


class AuthState(rx.State):
    authenticated: bool = False
    user_name: str = "(nome)"
    user_role: str = ""
    login_feedback: str = ""
    registration_feedback: str = ""
    employees: list[dict[str, Any]] = []
    employee_search: str = ""
    employee_editing_id: int = 0
    employee_delete_id: int = 0
    employee_delete_name: str = ""
    employee_delete_open: bool = False
    employee_delete_busy: bool = False
    employee_form_name: str = ""
    employee_form_email: str = ""
    employee_form_role: str = ""
    employee_form_password: str = ""
    product_tipo: str = ""
    product_marca: str = ""
    product_peso: str = ""
    product_codigo_de_barra: str = ""
    conference_codigo: str = ""
    conference_lote: str = ""
    conference_unidades: str = ""
    conference_validade: str = ""
    inventory_records: list[dict[str, str]] = []
    inventory_search: str = ""
    is_busy: bool = False
    _auth_token: str = ""
    _token_expires_at: float = 0.0

    @staticmethod
    def _error_message(
        error: XanoApiError,
        action: str,
        authentication: bool = False,
    ) -> str:
        if error.status_code in (401, 403):
            if authentication:
                return "Senha incorreta. Verifique sua senha e tente novamente."
            return "Você não tem autorização para realizar esta ação."
        if error.status_code == 409:
            return "Este e-mail já está cadastrado."
        if 400 <= error.status_code < 500:
            return "Verifique os dados informados e tente novamente."
        if error.status_code == 0:
            return "Não foi possível conectar ao Xano."
        return f"Não foi possível {action}. Tente novamente."

    @staticmethod
    def get_post_login_redirect(user_role: str | None) -> str | None:
        if user_role == "operator":
            return "/caixa"
        if user_role in {"owner", "manager"}:
            return "/"
        return None

    def _clear_session(self) -> None:
        self.authenticated = False
        self.user_name = "(nome)"
        self.user_role = ""
        self._auth_token = ""
        self._token_expires_at = 0.0

    def _set_user(self, user: Any) -> None:
        self.authenticated = True
        self.user_name = user.name
        self.user_role = user.role

    async def submit(self, form_data: dict[str, Any]) -> Any:
        email = str(form_data.get("user", "")).strip()
        password = str(form_data.get("senha", ""))
        self.login_feedback = ""

        if not email or not password:
            self.login_feedback = "Preencha usuário e senha para continuar."
            return

        self.is_busy = True
        try:
            token, _ = await login(email, password)
            user = await get_current_user(token)
            if user.is_active is False:
                self.login_feedback = "Este usuário está inativo."
                return
            self._auth_token = token
            self._token_expires_at = datetime.now(timezone.utc).timestamp() + 86400
            self._set_user(user)
            redirect = self.get_post_login_redirect(self.user_role)
            if redirect is not None:
                return rx.redirect(redirect)
            return None
        except XanoApiError as error:
            self._clear_session()
            self.login_feedback = self._error_message(
                error,
                "realizar o login",
                authentication=True,
            )
        finally:
            self.is_busy = False

    async def require_auth(self) -> Any:
        if not self._auth_token or self._token_expires_at <= datetime.now(timezone.utc).timestamp():
            self._clear_session()
            return rx.redirect("/login")

        try:
            user = await get_current_user(self._auth_token)
            if user.is_active is False:
                self._clear_session()
                return rx.redirect("/login")
            self._set_user(user)
        except XanoApiError:
            self._clear_session()
            return rx.redirect("/login")

    async def require_admin(self) -> Any:
        result = await self.require_auth()
        if result is not None:
            return result
        if self.user_role not in {"owner", "manager"}:
            return rx.redirect("/")

    async def require_admin_and_load_employees(self) -> Any:
        self.registration_feedback = ""
        result = await self.require_admin()
        if result is not None:
            return result
        await self.load_employees()

    def logout(self) -> Any:
        self._clear_session()
        self.login_feedback = ""
        self.registration_feedback = ""
        return rx.redirect("/login")

    async def register_employee(self, form_data: dict[str, Any]) -> None:
        self.registration_feedback = ""
        if self.user_role not in {"owner", "manager"}:
            self.registration_feedback = "Você não tem autorização para cadastrar funcionários."
            return

        name = str(form_data.get("name", "")).strip()
        email = str(form_data.get("email", "")).strip()
        password = str(form_data.get("password", ""))
        role = normalize_role(str(form_data.get("role", "")))

        if not name or not email or not password or role is None:
            self.registration_feedback = "Preencha os quatro campos com valores válidos."
            return

        password_error = validate_password(password)
        if password_error:
            self.registration_feedback = password_error
            return

        if not self._auth_token:
            self.registration_feedback = "Sua sessão expirou. Faça login novamente."
            return

        self.is_busy = True
        try:
            await create_employee(self._auth_token, name, email, password, role)
            self.registration_feedback = "Funcionário cadastrado com sucesso."
        except XanoApiError as error:
            if error.status_code == 401:
                self._clear_session()
            self.registration_feedback = self._error_message(error, "cadastrar o funcionário")
        finally:
            self.is_busy = False

    async def submit_employee_form(self, form_data: dict[str, Any]) -> None:
        self.employee_form_name = str(form_data.get("name", ""))
        self.employee_form_email = str(form_data.get("email", ""))
        self.employee_form_role = str(form_data.get("role", ""))
        self.employee_form_password = str(form_data.get("password", ""))
        if self.employee_editing_id:
            await self.save_employee()
            return
        await self.register_employee(form_data)
        if self.registration_feedback == "Funcionário cadastrado com sucesso.":
            await self.load_employees()
            self.employee_form_name = ""
            self.employee_form_email = ""
            self.employee_form_role = ""
            self.employee_form_password = ""

    async def load_employees(self) -> None:
        if not self._auth_token:
            self._clear_session()
            return
        try:
            self.employees = await list_employees(self._auth_token)
        except XanoApiError as error:
            if error.status_code == 401:
                self._clear_session()
            self.registration_feedback = self._error_message(
                error, "consultar os funcionários"
            )

    def set_employee_search(self, value: str) -> None:
        self.employee_search = value

    @rx.var
    def filtered_employees(self) -> list[dict[str, Any]]:
        query = self.employee_search.strip().casefold()
        if not query:
            return self.employees
        return [
            employee
            for employee in self.employees
            if query in str(employee.get("name", "")).casefold()
            or query in str(employee.get("email", "")).casefold()
            or query in str(employee.get("role", "")).casefold()
        ]

    @rx.var
    def employee_total(self) -> int:
        return len(self.employees)

    @rx.var
    def employee_filtered_total(self) -> int:
        return len(self.filtered_employees)

    @rx.var
    def employee_search_is_empty(self) -> bool:
        return not self.employee_search.strip()

    def start_employee_edit(self, employee: dict[str, Any]) -> None:
        self.employee_editing_id = int(employee.get("id", 0))
        self.employee_form_name = str(employee.get("name", ""))
        self.employee_form_email = str(employee.get("email", ""))
        self.employee_form_role = str(employee.get("role", ""))
        self.employee_form_password = ""
        self.registration_feedback = ""

    def cancel_employee_edit(self) -> None:
        self.employee_editing_id = 0
        self.employee_form_name = ""
        self.employee_form_email = ""
        self.employee_form_role = ""
        self.employee_form_password = ""

    def set_employee_form_name(self, value: str) -> None:
        self.employee_form_name = value

    def set_employee_form_email(self, value: str) -> None:
        self.employee_form_email = value

    def set_employee_form_role(self, value: str) -> None:
        self.employee_form_role = value

    def set_employee_form_password(self, value: str) -> None:
        self.employee_form_password = value

    async def save_employee(self) -> None:
        if self.user_role not in {"owner", "manager"}:
            self.registration_feedback = "Você não tem autorização para alterar funcionários."
            return
        name = self.employee_form_name.strip()
        email = self.employee_form_email.strip()
        role = normalize_role(self.employee_form_role)
        password = self.employee_form_password
        if not name or not email or role is None:
            self.registration_feedback = "Preencha nome, e-mail e cargo com valores válidos."
            return
        if password:
            password_error = validate_password(password)
            if password_error:
                self.registration_feedback = password_error
                return
        if not self._auth_token or not self.employee_editing_id:
            self.registration_feedback = "Selecione um funcionário para editar."
            return
        self.is_busy = True
        try:
            await update_employee(
                self._auth_token,
                self.employee_editing_id,
                name,
                email,
                role,
                password,
            )
            await self.load_employees()
            self.cancel_employee_edit()
            self.registration_feedback = "Funcionário atualizado com sucesso."
        except XanoApiError as error:
            if error.status_code == 401:
                self._clear_session()
            self.registration_feedback = self._error_message(
                error, "atualizar o funcionário"
            )
        finally:
            self.is_busy = False

    def open_employee_delete(self, employee: dict[str, Any]) -> None:
        if self.employee_delete_busy:
            return
        try:
            employee_id = int(employee.get("id", 0))
        except (TypeError, ValueError):
            self.registration_feedback = "Não foi possível identificar o funcionário."
            return
        if employee_id <= 0 or not any(
            str(record.get("id", "")) == str(employee_id)
            for record in self.employees
        ):
            self.registration_feedback = "Funcionário não encontrado na lista."
            return
        self.registration_feedback = ""
        self.employee_delete_id = employee_id
        self.employee_delete_name = str(employee.get("name", ""))
        self.employee_delete_open = True

    def close_employee_delete(self) -> None:
        if self.employee_delete_busy:
            return
        self.employee_delete_id = 0
        self.employee_delete_name = ""
        self.employee_delete_open = False

    async def confirm_employee_delete(self) -> None:
        if self.employee_delete_busy or not self.employee_delete_open:
            return
        if self.user_role not in {"owner", "manager"}:
            self.registration_feedback = "Você não tem autorização para excluir funcionários."
            self.close_employee_delete()
            return
        employee_id = self.employee_delete_id
        if not self._auth_token or employee_id <= 0:
            self.registration_feedback = "Sua sessão expirou. Faça login novamente."
            self.close_employee_delete()
            return
        if not any(
            str(employee.get("id", "")) == str(employee_id)
            for employee in self.employees
        ):
            self.registration_feedback = "Funcionário não encontrado na lista."
            self.close_employee_delete()
            return

        self.employee_delete_busy = True
        try:
            await delete_employee(self._auth_token, employee_id)
            self.employees = [
                employee
                for employee in self.employees
                if str(employee.get("id", "")) != str(employee_id)
            ]
            self.registration_feedback = "Funcionário excluído com sucesso."
        except XanoApiError as error:
            if error.status_code == 401:
                self._clear_session()
            if error.status_code == 404:
                self.registration_feedback = "O funcionário não foi encontrado ou já foi excluído."
            else:
                self.registration_feedback = self._error_message(
                    error, "excluir o funcionário"
                )
        finally:
            self.employee_delete_busy = False
            self.close_employee_delete()

    def set_product_tipo(self, value: str) -> None:
        self.product_tipo = value

    def set_product_marca(self, value: str) -> None:
        self.product_marca = value

    def set_product_peso(self, value: str) -> None:
        self.product_peso = value

    def set_product_codigo_de_barra(self, value: str) -> None:
        self.product_codigo_de_barra = value

    def _clear_product_form(self) -> None:
        self.product_tipo = ""
        self.product_marca = ""
        self.product_peso = ""
        self.product_codigo_de_barra = ""

    async def register_product(self) -> Any:
        if self.user_role not in {"owner", "manager"}:
            return rx.toast.error(
                "Você não tem autorização para cadastrar produtos."
            )
        if not self._auth_token:
            self._clear_session()
            return rx.redirect("/login")

        tipo = self.product_tipo.strip()
        marca = self.product_marca.strip()
        peso_text = self.product_peso.strip()
        codigo_de_barra = self.product_codigo_de_barra.strip()
        if not is_valid_product_text(tipo):
            return rx.toast.error(
                "Corrija o campo Tipo: use somente letras e espaços."
            )
        if not is_valid_product_text(marca):
            return rx.toast.error(
                "Corrija o campo Marca: use somente letras e espaços."
            )
        if not peso_text or not codigo_de_barra:
            return rx.toast.error("Preencha os quatro campos para cadastrar o produto.")

        peso = parse_product_weight(peso_text)
        if peso is None:
            return rx.toast.error("Informe um peso numérico válido.")

        if self.is_busy:
            return
        self.is_busy = True
        try:
            await create_product(
                self._auth_token,
                tipo,
                marca,
                peso,
                codigo_de_barra,
            )
            self._clear_product_form()
            return rx.toast.success("Produto cadastrado com sucesso.")
        except XanoApiError as error:
            if error.status_code == 401:
                self._clear_session()
                return rx.redirect("/login")
            if error.status_code in {400, 409}:
                if "duplicate" in error.code.lower() or "unique" in error.message.lower():
                    return rx.toast.error(
                        "Já existe um produto com este código de barras."
                    )
                return rx.toast.error(
                    "Os dados do produto foram rejeitados pelo Xano."
                )
            if error.status_code == 0:
                return rx.toast.error("Não foi possível conectar ao Xano.")
            return rx.toast.error(error.message)
        finally:
            self.is_busy = False

    def set_conference_codigo(self, value: str) -> None:
        self.conference_codigo = value

    def set_conference_lote(self, value: str) -> None:
        self.conference_lote = value

    def set_conference_unidades(self, value: str) -> None:
        self.conference_unidades = value

    def set_conference_validade(self, value: str) -> None:
        self.conference_validade = value

    def set_inventory_search(self, value: str) -> None:
        self.inventory_search = value

    @rx.var
    def filtered_inventory(self) -> list[dict[str, str]]:
        query = self.inventory_search.strip().lower()
        if not query:
            return self.inventory_records
        return [
            record
            for record in self.inventory_records
            if query in " ".join(record.values()).lower()
        ]

    async def require_admin_and_load_inventory(self) -> Any:
        result = await self.require_admin()
        if result is not None:
            return result
        return await self.load_inventory()

    async def load_inventory(self) -> Any:
        if not self._auth_token:
            self._clear_session()
            return rx.redirect("/login")
        try:
            products = await list_products(self._auth_token)
            inventory = await list_inventory(self._auth_token)
            products_by_id = {
                product.get("id"): product
                for product in products
                if isinstance(product.get("id"), int)
            }
            self.inventory_records = [
                {
                    "name": self._inventory_product_name(
                        products_by_id.get(record.get("produtos_id"))
                    ),
                    "batch": str(record.get("lote") or ""),
                    "quantity": str(record.get("unidades") or ""),
                    "barcode": str(
                        products_by_id.get(record.get("produtos_id"), {}).get(
                            "codigo_de_barra",
                            "",
                        )
                    ),
                    "expiration": str(record.get("validade") or ""),
                }
                for record in inventory
            ]
        except XanoApiError as error:
            if error.status_code == 401:
                self._clear_session()
                return rx.redirect("/login")
            return rx.toast.error(error.message)

    @staticmethod
    def _inventory_product_name(product: dict[str, Any] | None) -> str:
        if not product:
            return "Produto não encontrado"
        product_name = [
            str(product.get(field, "")).strip()
            for field in ("tipo", "marca")
            if str(product.get(field, "")).strip()
        ]
        weight = str(product.get("peso", "")).strip()
        if weight:
            product_name.append(f"{weight} g")
        return " ".join(product_name)

    async def add_inventory(self) -> Any:
        if self.user_role not in {"owner", "manager"}:
            return rx.toast.error(
                "Você não tem autorização para atualizar o estoque."
            )
        if self.is_busy:
            return
        codigo = self.conference_codigo.strip()
        lote = self.conference_lote.strip()
        unidades = parse_inventory_units(self.conference_unidades)
        validade = parse_inventory_date(self.conference_validade)
        if not codigo or not lote:
            return rx.toast.error("Informe o código e o lote do produto.")
        if unidades is None:
            return rx.toast.error("Informe uma quantidade inteira maior que zero.")
        if validade is None:
            return rx.toast.error("Informe uma data de validade válida.")
        if not self._auth_token:
            self._clear_session()
            return rx.redirect("/login")

        self.is_busy = True
        try:
            async with INVENTORY_OPERATION_LOCK:
                products = await list_products(self._auth_token)
                product = next(
                    (
                        item
                        for item in products
                        if item.get("codigo_de_barra") == codigo
                    ),
                    None,
                )
                if product is None or not isinstance(product.get("id"), int):
                    return rx.toast.error("Nenhum produto encontrado para este código.")

                inventory = await list_inventory(self._auth_token)
                existing = find_inventory_record(inventory, product["id"], validade)
                if existing is not None and isinstance(existing.get("id"), int):
                    current_units = parse_inventory_units(
                        str(existing.get("unidades", ""))
                    )
                    if current_units is None:
                        return rx.toast.error(
                            "O Xano retornou uma quantidade inválida no estoque."
                        )
                    await update_inventory_lot(
                        self._auth_token,
                        existing["id"],
                        current_units + unidades,
                    )
                else:
                    await create_inventory_lot(
                        self._auth_token,
                        product["id"],
                        unidades,
                        validade,
                        lote,
                    )
                self.conference_codigo = ""
                self.conference_lote = ""
                self.conference_unidades = ""
                self.conference_validade = ""
                await self.load_inventory()
                return rx.toast.success("Estoque atualizado com sucesso.")
        except XanoApiError as error:
            if error.status_code == 401:
                self._clear_session()
                return rx.redirect("/login")
            return rx.toast.error(error.message)
        finally:
            self.is_busy = False


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


@rx.page(route="/login")
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
                            AuthState.login_feedback,
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
                    on_submit=AuthState.submit,
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
    "prices": "/precos",
}

SIDEBAR_ITEMS = (
    ("Início", "home"),
    ("Estoque", "inventory"),
    ("Conferência", "receiving"),
    ("Produto", "products"),
    ("Relatórios", "reports"),
    ("Cadastro", "registration"),
    ("Preços", "prices"),
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
    {
        "title": "Preço",
        "description": "Cadastre e consulte os preços dos produtos",
        "icon": "tag",
        "color": "#8B5CF6",
        "destination": "prices",
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

def sidebar_item(label: str, destination: str, is_active: bool = False) -> rx.Component:
    return rx.link(
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
    )


def sidebar(
    active_destination: str = "home",
    fixed_for_registration: bool = False,
) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(
                AuthState.user_name,
                font_size="1.2rem",
                font_weight="700",
                color="white",
                width="100%",
                padding="0.65rem 0.75rem 0.9rem",
            ),
            rx.vstack(
                *[
                    sidebar_item(
                        label,
                        destination,
                        is_active=(destination == active_destination),
                    )
                    for label, destination in SIDEBAR_ITEMS
                ],
                width="100%",
                gap="0.4rem",
            ),
            rx.button(
                rx.hstack(
                    rx.icon(
                        "log-out",
                        size=18,
                        color="white",
                        stroke_width=2,
                        aria_hidden="true",
                    ),
                    rx.text("Sair"),
                    width="100%",
                    align="center",
                    justify="start",
                    gap="0.65rem",
                ),
                type="button",
                on_click=AuthState.logout,
                variant="ghost",
                width="100%",
                min_width="0",
                margin="0",
                box_sizing="border-box",
                padding="0.72rem 1.15rem",
                border_radius="0.45rem",
                color="white",
                font_size="0.98rem",
                font_weight="500",
                cursor="pointer",
                background="#4D8DF7",
                class_name="sidebar-logout",
                _hover={"background": "#5B98F8"},
                _focus_visible={
                    "outline": "3px solid rgba(255, 255, 255, 0.88)",
                    "outline_offset": "2px",
                },
                _active={"background": "#3D7FEA"},
            ),
            width="100%",
            height="100%",
            min_height="100%",
            align="stretch",
            justify="between",
            gap="1.5rem",
        ),
        width="16rem",
        min_width="16rem",
        min_height="100dvh",
        height="100dvh" if fixed_for_registration else "auto",
        padding="2.3rem 1.15rem",
        box_sizing="border-box",
        display="flex",
        class_name="dashboard-sidebar",
        background="#3B82F6",
        color="white",
        position="fixed" if fixed_for_registration else "relative",
        top="0" if fixed_for_registration else "auto",
        left="0" if fixed_for_registration else "auto",
        z_index="10" if fixed_for_registration else "auto",
    )


def dashboard_header(subtitle: str = "Aqui está um resumo do seu mercado hoje.") -> rx.Component:
    return rx.vstack(
        rx.heading(
            "Olá, ",
            AuthState.user_name,
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
                for card in DASHBOARD_CARDS
            ],
            width="100%",
            max_width="62rem",
            display="grid",
            grid_template_columns="1fr",
            class_name="dashboard-card-grid dashboard-card-grid-primary",
            gap="2.5rem",
        ),
        width="100%",
        align="center",
    )


class PricesState(rx.State):
    mock_products: list[dict[str, str]] = [
        {
            "product": "Salgadinho Doritos 37 g",
            "barcode": "7892840816469",
            "type": "Salgadinho",
            "brand": "Doritos",
            "weight": "37 g",
        },
        {
            "product": "Arroz Tio Urbano 5000 g",
            "barcode": "7896290300011",
            "type": "Arroz",
            "brand": "Tio Urbano",
            "weight": "5000 g",
        },
        {
            "product": "Margarina Qualy 500 g",
            "barcode": "7891000205023",
            "type": "Margarina",
            "brand": "Qualy",
            "weight": "500 g",
        },
    ]
    mock_prices: list[dict[str, str]] = [
        {
            "product": "Salgadinho Doritos 37 g",
            "barcode": "7892840816469",
            "brand": "Doritos",
            "price": "R$ 5,99",
            "date": "16/10/2026",
        },
        {
            "product": "Arroz Tio Urbano 5000 g",
            "barcode": "7896290300011",
            "brand": "Tio Urbano",
            "price": "R$ 24,90",
            "date": "16/10/2026",
        },
        {
            "product": "Margarina Qualy 500 g",
            "barcode": "7891000205023",
            "brand": "Qualy",
            "price": "R$ 8,49",
            "date": "16/10/2026",
        },
    ]
    barcode_input: str = ""
    price_input: str = ""
    price_search_input: str = ""
    applied_price_search: str = ""
    selected_product: dict[str, str] = {}
    has_selected_product: bool = False
    feedback: str = ""
    feedback_is_error: bool = False

    def set_barcode_input(self, value: str) -> None:
        self.barcode_input = value

    def set_price_input(self, value: str) -> None:
        self.price_input = value

    def set_price_search_input(self, value: str) -> None:
        self.price_search_input = value

    def search_mock_product(self) -> None:
        barcode = self.barcode_input.strip()
        product = next(
            (item for item in self.mock_products if item["barcode"] == barcode),
            None,
        )
        self.selected_product = product or {}
        self.has_selected_product = product is not None
        self.feedback = (
            "Produto encontrado."
            if product is not None
            else "Nenhum produto encontrado para este código de barras."
        )
        self.feedback_is_error = product is None

    def link_mock_price(self) -> None:
        if not self.has_selected_product:
            self.feedback = "Pesquise um produto pelo código de barras primeiro."
            self.feedback_is_error = True
            return

        try:
            price = Decimal(self.price_input.strip().replace(",", "."))
        except InvalidOperation:
            price = Decimal("0")
        if not price.is_finite() or price <= 0:
            self.feedback = "Digite um preço válido."
            self.feedback_is_error = True
            return

        product = self.selected_product
        formatted_price = f"R$ {price:.2f}".replace(".", ",")
        updated = {
            "product": product["product"],
            "barcode": product["barcode"],
            "brand": product["brand"],
            "price": formatted_price,
            "date": "16/10/2026",
        }
        existing_index = next(
            (
                index
                for index, record in enumerate(self.mock_prices)
                if record["barcode"] == product["barcode"]
            ),
            None,
        )
        if existing_index is None:
            self.mock_prices = [updated, *self.mock_prices]
        else:
            self.mock_prices[existing_index] = updated
            self.mock_prices = list(self.mock_prices)
        self.feedback = "Preço vinculado localmente."
        self.feedback_is_error = False
        self.price_input = ""

    def search_mock_prices(self) -> None:
        self.applied_price_search = self.price_search_input.strip().casefold()

    @rx.var
    def filtered_mock_prices(self) -> list[dict[str, str]]:
        query = self.applied_price_search
        if not query:
            return self.mock_prices
        return [
            price
            for price in self.mock_prices
            if query in price["product"].casefold()
            or query in price["barcode"].casefold()
            or query in price["brand"].casefold()
        ]


def prices_table_row(price: dict[str, str]) -> rx.Component:
    return rx.box(
        rx.text(price["product"], color="#172033", min_width="0", overflow_wrap="anywhere"),
        rx.text(price["barcode"], color="#172033", min_width="0", overflow_wrap="anywhere"),
        rx.text(price["price"], color="#172033", min_width="0"),
        rx.text(price["date"], color="#172033", min_width="0"),
        display="grid",
        grid_template_columns="2fr 1.35fr 0.8fr 0.9fr",
        gap="0.75rem",
        min_width="42rem",
        align_items="center",
        padding="0.85rem 0.25rem",
        border_bottom="1px solid #EEF1F5",
    )


def price_field(label: str, control: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(label, color="#172033", font_weight="600", font_size="0.92rem"),
        control,
        width="100%",
        align="stretch",
        gap="0.45rem",
    )


def prices_panel() -> rx.Component:
    input_style = {
        "width": "100%",
        "height": "3.1rem",
        "padding": "0 1rem",
        "text_align": "left",
        "border_radius": "0.7rem",
        "border": "1px solid #E5E7EB",
        "background": "#D9D9D9",
        "color": "#000000",
        "font_size": "0.98rem",
        "_placeholder": {"color": "#000000", "opacity": "1"},
        "_focus": {
            "background": "#D9D9D9",
            "border_color": "#93C5FD",
            "color": "#000000",
        },
    }
    primary_button_style = {
        "height": "3.1rem",
        "border_radius": "0.7rem",
        "background": "#3B82F6",
        "color": "white",
        "font_weight": "700",
        "box_shadow": "0 8px 18px rgba(59, 130, 246, 0.2)",
        "_hover": {"background": "#2563EB"},
    }

    return rx.vstack(
        rx.box(
            rx.vstack(
                rx.heading("Cadastar Preço de Produto", size="5", color="#172033"),
                rx.text(
                    "Relacione um código de barras já cadastrado a um preço.",
                    color="#7A8496",
                    font_size="0.95rem",
                ),
                rx.box(
                    price_field(
                        "Código de barras",
                        rx.hstack(
                            rx.input(
                                placeholder="Digite o código de barras",
                                aria_label="Código de barras do produto",
                                value=PricesState.barcode_input,
                                on_change=PricesState.set_barcode_input,
                                **input_style,
                            ),
                            rx.button(
                                rx.icon("search", size=19),
                                aria_label="Pesquisar código de barras",
                                on_click=PricesState.search_mock_product,
                                width="3.1rem",
                                min_width="3.1rem",
                                **primary_button_style,
                            ),
                            width="100%",
                            gap="0.6rem",
                        ),
                    ),
                    price_field(
                        "Preço",
                        rx.input(
                            type="text",
                            input_mode="decimal",
                            placeholder="R$ 0,00",
                            aria_label="Preço do produto",
                            value=PricesState.price_input,
                            on_change=PricesState.set_price_input,
                            **input_style,
                        ),
                    ),
                    class_name="prices-fields-grid",
                    display="grid",
                    grid_template_columns="minmax(0, 1fr)",
                    gap="1rem",
                    width="100%",
                ),
                rx.button(
                    "Vincular Preço",
                    type="button",
                    on_click=PricesState.link_mock_price,
                    width="100%",
                    **primary_button_style,
                ),
                rx.cond(
                    PricesState.has_selected_product,
                    rx.box(
                        rx.vstack(
                            rx.heading("Produto selecionado", size="3", color="#172033"),
                            rx.box(
                                rx.vstack(
                                    rx.text("Produto", color="#7A8496", font_size="0.82rem"),
                                    rx.text(
                                        PricesState.selected_product["product"],
                                        color="#172033",
                                        font_weight="600",
                                    ),
                                    align="start",
                                    gap="0.3rem",
                                ),
                                rx.vstack(
                                    rx.text("Tipo", color="#7A8496", font_size="0.82rem"),
                                    rx.text(PricesState.selected_product["type"], color="#172033"),
                                    align="start",
                                    gap="0.3rem",
                                ),
                                rx.vstack(
                                    rx.text("Marca", color="#7A8496", font_size="0.82rem"),
                                    rx.text(PricesState.selected_product["brand"], color="#172033"),
                                    align="start",
                                    gap="0.3rem",
                                ),
                                rx.vstack(
                                    rx.text("Gramas", color="#7A8496", font_size="0.82rem"),
                                    rx.text(PricesState.selected_product["weight"], color="#172033"),
                                    align="start",
                                    gap="0.3rem",
                                ),
                                class_name="prices-selected-details",
                                display="grid",
                                grid_template_columns="minmax(0, 1fr)",
                                gap="1rem",
                                width="100%",
                            ),
                            align="stretch",
                            gap="0.85rem",
                            width="100%",
                        ),
                        width="100%",
                        padding="1rem",
                        background="#F7F9FC",
                        border="1px solid #E5E7EB",
                        border_radius="0.7rem",
                    ),
                    rx.fragment(),
                ),
                rx.text(
                    PricesState.feedback,
                    color=rx.cond(PricesState.feedback_is_error, "#DC2626", "#15803D"),
                    role="status",
                    min_height="1.2rem",
                ),
                width="100%",
                align="stretch",
                gap="1rem",
            ),
            width="100%",
            padding="clamp(1.25rem, 2.5vw, 2rem)",
            background="white",
            border_radius="1rem",
            box_shadow="0 10px 28px rgba(23, 32, 51, 0.08)",
        ),
        rx.divider(width="100%", border_color="#DDE3EC"),
        rx.box(
            rx.vstack(
                rx.heading("Consultar Preços", size="5", color="#172033"),
                rx.hstack(
                    rx.input(
                        placeholder="Digite o código de barras, nome do produto ou marca",
                        aria_label="Consultar preços por código, nome ou marca",
                        value=PricesState.price_search_input,
                        on_change=PricesState.set_price_search_input,
                        **input_style,
                    ),
                    rx.button(
                        rx.hstack(rx.text("Consultar"), rx.icon("search", size=18), gap="0.5rem"),
                        type="button",
                        on_click=PricesState.search_mock_prices,
                        **primary_button_style,
                        padding="0 1.2rem",
                    ),
                    width="100%",
                    gap="0.75rem",
                    align="center",
                    class_name="prices-search-row",
                ),
                rx.heading("Preços cadastrados", size="4", color="#172033", margin_top="0.5rem"),
                rx.box(
                    rx.text("Produto", font_weight="700", color="#5B6475", min_width="0"),
                    rx.text("Código de barras", font_weight="700", color="#5B6475", min_width="0"),
                    rx.text("Preço", font_weight="700", color="#5B6475", min_width="0"),
                    rx.text("Cadastrado em", font_weight="700", color="#5B6475", min_width="0"),
                    display="grid",
                    grid_template_columns="2fr 1.35fr 0.8fr 0.9fr",
                    gap="0.75rem",
                    min_width="42rem",
                    padding="0.85rem 0.25rem",
                    border_bottom="1px solid #DDE3EC",
                ),
                rx.box(
                    rx.cond(
                        PricesState.filtered_mock_prices.length() > 0,
                        rx.foreach(PricesState.filtered_mock_prices, prices_table_row),
                        rx.text(
                            "Nenhum preço encontrado.",
                            color="#5B6475",
                            text_align="center",
                            padding="1.5rem 0",
                        ),
                    ),
                    width="100%",
                    overflow_x="auto",
                    max_height="22rem",
                    overflow_y="auto",
                    class_name="prices-table-scroll",
                ),
                width="100%",
                align="stretch",
                gap="1rem",
            ),
            width="100%",
            padding="clamp(1.25rem, 2.5vw, 2rem)",
            background="white",
            border_radius="1rem",
            box_shadow="0 10px 28px rgba(23, 32, 51, 0.08)",
        ),
        width="100%",
        max_width="62rem",
        margin="0 auto",
        align="stretch",
        gap="1.5rem",
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


def cashier_table_cell(
    content: str,
    *,
    header: bool = False,
    last: bool = False,
) -> rx.Component:
    return rx.box(
        rx.text(
            content,
            color="#172033",
            font_size="clamp(0.7rem, 1.3vw, 0.92rem)",
            font_weight="700" if header else "400",
            line_height="1.25",
            text_align="center",
            width="100%",
        ),
        padding="0.8rem 0.55rem",
        min_width="0",
        min_height="2.9rem",
        display="flex",
        align_items="center",
        justify_content="center",
        border_right="none" if last else "1px solid #DDE3EC",
    )


def cashier_table() -> rx.Component:
    columns = ("Nome", "Qnt.", "Código", "Valor Unit.", "Total")
    empty_rows = [("", "", "", "", "") for _ in range(6)]
    header = [
        cashier_table_cell(
            column,
            header=True,
            last=index == len(columns) - 1,
        )
        for index, column in enumerate(columns)
    ]
    rows = [
        cashier_table_cell(value, last=index == len(columns) - 1)
        for row in empty_rows
        for index, value in enumerate(row)
    ]

    return rx.box(
        rx.box(
            *header,
            display="grid",
            grid_template_columns="2fr 0.7fr 1.2fr 1fr 1fr",
            border_bottom="1px solid #BFC8D6",
        ),
        rx.box(
            *rows,
            display="grid",
            grid_template_columns="2fr 0.7fr 1.2fr 1fr 1fr",
            grid_template_rows="repeat(6, minmax(2.9rem, 1fr))",
        ),
        width="100%",
        overflow_x="auto",
        border="1px solid #E3E8F0",
        border_radius="0.65rem",
    )


def cashier_page_content() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.box(
                rx.vstack(
                    rx.image(
                        src="/logo_bipsystem_branca.png",
                        alt="Logo BIPSYSTEM",
                        width="min(13rem, 70%)",
                        height="auto",
                    ),
                    rx.text(
                        "BIPSYSTEM",
                        color="white",
                        font_size="clamp(1.5rem, 3vw, 2.5rem)",
                        font_weight="800",
                        letter_spacing="0.08em",
                        text_align="center",
                    ),
                    rx.text(
                        "Automação Comercial",
                        color="rgba(255, 255, 255, 0.88)",
                        font_size="clamp(0.95rem, 1.8vw, 1.15rem)",
                        text_align="center",
                    ),
                    gap="0.7rem",
                    align="center",
                ),
                class_name="cashier-brand",
                display="flex",
                align_items="center",
                justify_content="center",
                width="28%",
                min_width="13rem",
                padding="2rem 1rem",
            ),
            rx.box(
                rx.hstack(
                    rx.heading(
                        "BIPSYSTEM",
                        color="white",
                        font_family="'Segoe Script', 'Brush Script MT', cursive",
                        font_size="clamp(2rem, 4vw, 3.1rem)",
                        font_weight="700",
                        line_height="1",
                    ),
                    rx.text(
                        "bipsystem.com.br",
                        color="rgba(255, 255, 255, 0.9)",
                        font_size="0.9rem",
                        margin_left="auto",
                    ),
                    width="100%",
                    align="center",
                    gap="1rem",
                ),
                rx.vstack(
                    rx.box(
                        rx.hstack(
                            rx.text(
                                "Total:",
                                color="#172033",
                                font_size="1.1rem",
                                font_weight="700",
                            ),
                            rx.text(
                                "1234,00 R$",
                                color="#172033",
                                font_size="clamp(1.7rem, 4vw, 2.8rem)",
                                font_weight="800",
                                margin_left="auto",
                            ),
                            width="100%",
                            align="center",
                        ),
                        width="100%",
                        background="white",
                        border_radius="0.9rem",
                        box_shadow="0 8px 22px rgba(23, 32, 51, 0.12)",
                        padding="1.25rem clamp(1.1rem, 3vw, 2rem)",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.heading(
                                "Itens da compra",
                                color="#172033",
                                font_size="1.1rem",
                                font_weight="700",
                                margin_bottom="0.15rem",
                            ),
                            cashier_table(),
                            width="100%",
                            align="stretch",
                            gap="0.9rem",
                        ),
                        width="100%",
                        background="white",
                        border_radius="0.9rem",
                        box_shadow="0 8px 22px rgba(23, 32, 51, 0.12)",
                        padding="clamp(1rem, 2.5vw, 1.6rem)",
                    ),
                    width="100%",
                    gap="1.2rem",
                    align="stretch",
                ),
                class_name="cashier-workspace",
                width="72%",
                min_width="0",
                padding="clamp(1rem, 2vw, 2rem) 0",
                gap="clamp(1.5rem, 4vw, 3rem)",
                display="flex",
                flex_direction="column",
            ),
            class_name="cashier-shell",
            width="100%",
            max_width="90rem",
            min_height="calc(100vh - 3rem)",
            margin="0 auto",
            align="stretch",
            gap="clamp(1rem, 3vw, 3rem)",
        ),
        class_name="cashier-page",
        width="100%",
        min_height="100dvh",
        padding="1.5rem clamp(1rem, 4vw, 4rem)",
        background="#307CE8",
        overflow="auto",
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
            rx.heading(
                rx.cond(
                    AuthState.employee_editing_id > 0,
                    "Editar Funcionário",
                    "Adicionar Funcionário",
                ),
                size="5",
                color="#172033",
                text_align="center",
                width="100%",
            ),
            rx.form(
                rx.input(
                    type="text",
                    name="name",
                    placeholder="Digite o nome do funcionário",
                    aria_label="Digite o nome do funcionário",
                    value=AuthState.employee_form_name,
                    on_change=AuthState.set_employee_form_name,
                    class_name="registration-form-input",
                    **input_style,
                ),
                rx.input(
                    type="email",
                    name="email",
                    placeholder="Digite o e-mail do funcionário",
                    aria_label="Digite o e-mail do funcionário",
                    value=AuthState.employee_form_email,
                    on_change=AuthState.set_employee_form_email,
                    class_name="registration-form-input",
                    **input_style,
                ),
                rx.input(
                    type="password",
                    name="password",
                    placeholder=rx.cond(
                        AuthState.employee_editing_id > 0,
                        "Nova senha (opcional)",
                        "Digite a senha desejada",
                    ),
                    aria_label="Digite a senha desejada",
                    value=AuthState.employee_form_password,
                    on_change=AuthState.set_employee_form_password,
                    class_name="registration-form-input",
                    **input_style,
                ),
                rx.select(
                    ["Proprietário", "Operador", "Admin"],
                    name="role",
                    placeholder="Digite a função do funcionário",
                    aria_label="Digite a função do funcionário",
                    value=AuthState.employee_form_role,
                    on_change=AuthState.set_employee_form_role,
                    class_name="registration-form-input",
                    justify_content="center",
                    **input_style,
                ),
                rx.button(
                    rx.cond(
                        AuthState.employee_editing_id > 0,
                        "Salvar alterações",
                        "Cadastrar Funcionário",
                    ),
                    type="submit",
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
                rx.text(
                    AuthState.registration_feedback,
                    role="status",
                    color="#172033",
                    font_size="0.82rem",
                    line_height="1.35",
                    text_align="center",
                    min_height="1.15rem",
                ),
                width="100%",
                margin="0 auto",
                gap="1rem",
                align="stretch",
                display="flex",
                flex_direction="column",
                on_submit=AuthState.submit_employee_form,
                reset_on_submit=False,
            ),
            rx.cond(
                AuthState.employee_editing_id > 0,
                rx.button(
                    "Cancelar edição",
                    type="button",
                    on_click=AuthState.cancel_employee_edit,
                    width="100%",
                    height="2.6rem",
                    border_radius="0.7rem",
                    background="#E5E7EB",
                    color="#172033",
                ),
                rx.fragment(),
            ),
            width="100%",
            max_width="42rem",
            gap="1.5rem",
            align="center",
            margin="0 auto",
        ),
        width="100%",
        max_width="none",
        margin="0",
        background="white",
        border_radius="1rem",
        box_shadow="0 10px 28px rgba(23, 32, 51, 0.08)",
        padding="clamp(1.5rem, 3vw, 2.25rem)",
        height="31rem",
        box_sizing="border-box",
        class_name="registration-form-panel",
    )


def employee_row(employee: dict[str, Any]) -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.text(
                employee["name"],
                color="#172033",
                min_width="0",
                overflow_wrap="anywhere",
            ),
            rx.text(
                employee["email"],
                color="#172033",
                min_width="0",
                overflow_wrap="anywhere",
            ),
            rx.text(employee["role"], color="#172033", min_width="0"),
            rx.hstack(
                rx.button(
                    rx.icon("pencil", size=16),
                    aria_label="Editar funcionário",
                    on_click=AuthState.start_employee_edit(employee),
                    background="#3B82F6",
                    color="white",
                    width="2rem",
                    min_width="2rem",
                    height="2rem",
                    padding="0",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    box_sizing="border-box",
                ),
                rx.button(
                    rx.icon("trash-2", size=16),
                    aria_label="Excluir funcionário",
                    on_click=AuthState.open_employee_delete(employee),
                    background="#DC2626",
                    color="white",
                    width="2rem",
                    min_width="2rem",
                    height="2rem",
                    padding="0",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    box_sizing="border-box",
                ),
                gap="0.25rem",
                width="4.25rem",
                min_width="4.25rem",
                justify="center",
            ),
            display="grid",
            grid_template_columns="minmax(0, 1.2fr) minmax(0, 1.6fr) minmax(5rem, 0.8fr) 4.5rem",
            gap="0.5rem",
            align_items="center",
            min_width="0",
            padding="0.8rem 0.2rem",
            border_bottom="1px solid #EEF1F5",
        ),
        rx.cond(
            AuthState.employee_delete_open,
            rx.cond(
                AuthState.employee_delete_id == employee["id"],
                rx.box(
                    rx.vstack(
                        rx.text(
                            "Excluir funcionário?",
                            font_weight="700",
                            color="#172033",
                        ),
                        rx.text(
                            "Esta ação é permanente e não pode ser desfeita. ",
                            "O funcionário ",
                            AuthState.employee_delete_name,
                            " será removido do sistema.",
                            color="#5B6475",
                            font_size="0.85rem",
                        ),
                        rx.hstack(
                            rx.button(
                                "Cancelar",
                                on_click=AuthState.close_employee_delete,
                                disabled=AuthState.employee_delete_busy,
                                background="#E5E7EB",
                                color="#172033",
                                flex="1",
                            ),
                            rx.button(
                                "Excluir",
                                on_click=AuthState.confirm_employee_delete,
                                disabled=AuthState.employee_delete_busy,
                                background="#DC2626",
                                color="white",
                                flex="1",
                            ),
                            width="min(100%, 18rem)",
                            gap="0.75rem",
                        ),
                        align="start",
                        gap="0.5rem",
                    ),
                    width="100%",
                    padding="0.85rem 1rem",
                    background="#FFF7F7",
                    border="1px solid #FECACA",
                    border_radius="0.65rem",
                ),
                rx.fragment(),
            ),
            rx.fragment(),
        ),
        width="100%",
        align="stretch",
        gap="0.5rem",
    )


def registration_list_panel() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading(
                "Funcionários cadastrados",
                size="5",
                color="#172033",
                text_align="left",
                width="100%",
            ),
            rx.hstack(
                rx.input(
                    placeholder="Pesquisar por nome, e-mail ou cargo",
                    aria_label="Pesquisar funcionários",
                    value=AuthState.employee_search,
                    on_change=AuthState.set_employee_search,
                    width="100%",
                    height="3.1rem",
                    background="#F7F9FC",
                    color="#172033",
                    border="1px solid #E5E7EB",
                    border_radius="0.7rem",
                    class_name="registration-search-input",
                ),
                rx.text(
                    rx.cond(
                        AuthState.employee_search_is_empty,
                        rx.fragment("Total: ", AuthState.employee_total),
                        rx.fragment(
                            "Exibindo: ",
                            AuthState.employee_filtered_total,
                            " de ",
                            AuthState.employee_total,
                        ),
                    ),
                    color="#5B6475",
                    font_size="0.85rem",
                    white_space="nowrap",
                ),
                width="100%",
                align="center",
                gap="1rem",
            ),
            rx.box(
                rx.box(
                    rx.text("Nome", font_weight="700", color="#5B6475", min_width="0"),
                    rx.text("E-mail", font_weight="700", color="#5B6475", min_width="0"),
                    rx.text("Cargo", font_weight="700", color="#5B6475", min_width="0"),
                    rx.text("Ações", font_weight="700", color="#5B6475", min_width="0"),
                    display="grid",
                    grid_template_columns="minmax(0, 1.2fr) minmax(0, 1.6fr) minmax(5rem, 0.8fr) 4.5rem",
                    gap="0.5rem",
                    min_width="0",
                    padding="0.8rem 0.2rem",
                    border_bottom="1px solid #DDE3EC",
                ),
                rx.cond(
                    AuthState.employee_filtered_total > 0,
                    rx.foreach(AuthState.filtered_employees, employee_row),
                    rx.text(
                        "Nenhum funcionário encontrado",
                        color="#5B6475",
                        text_align="center",
                        padding="2rem 0",
                    ),
                ),
                width="100%",
                overflow_y="auto",
                overflow_x="auto",
                flex="1",
                min_height="0",
                class_name="registration-employee-scroll",
            ),
            rx.text(
                AuthState.registration_feedback,
                role="status",
                color="#172033",
                font_size="0.82rem",
                width="100%",
                min_height="1.15rem",
            ),
            width="100%",
            gap="0.85rem",
            align="stretch",
            height="100%",
        ),
        width="100%",
        max_width="none",
        margin="0",
        background="white",
        border_radius="1rem",
        box_shadow="0 10px 28px rgba(23, 32, 51, 0.08)",
        padding="clamp(1.5rem, 3vw, 2.25rem)",
        height="31rem",
        box_sizing="border-box",
        class_name="registration-list-panel",
    )


def registration_panels() -> rx.Component:
    return rx.box(
        registration_form_panel(),
        registration_list_panel(),
        class_name="registration-panels",
        width="100%",
        display="grid",
        grid_template_columns="minmax(0, 1fr)",
        gap="1.5rem",
        align_items="stretch",
        position="relative",
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
                    value=AuthState.product_tipo,
                    on_change=AuthState.set_product_tipo,
                    **input_style,
                ),
                rx.input(
                    type="text",
                    placeholder="Digite a marca do produto",
                    aria_label="Digite a marca do produto",
                    class_name="registration-form-input",
                    value=AuthState.product_marca,
                    on_change=AuthState.set_product_marca,
                    **input_style,
                ),
                rx.input(
                    type="text",
                    placeholder="Digite o peso do produto (g)",
                    aria_label="Digite o peso do produto (g)",
                    class_name="registration-form-input",
                    value=AuthState.product_peso,
                    on_change=AuthState.set_product_peso,
                    **input_style,
                ),
                rx.input(
                    type="text",
                    placeholder="Digite o código de barra do produto",
                    aria_label="Digite o código de barra do produto",
                    class_name="registration-form-input",
                    value=AuthState.product_codigo_de_barra,
                    on_change=AuthState.set_product_codigo_de_barra,
                    **input_style,
                ),
                rx.button(
                    "Cadastrar",
                    type="button",
                    on_click=AuthState.register_product,
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
                    value=AuthState.conference_codigo,
                    on_change=AuthState.set_conference_codigo,
                    **input_style,
                ),
                rx.input(
                    type="text",
                    placeholder="Lote",
                    aria_label="Lote",
                    class_name="registration-form-input",
                    value=AuthState.conference_lote,
                    on_change=AuthState.set_conference_lote,
                    **input_style,
                ),
                rx.input(
                    type="number",
                    placeholder="Unidades",
                    aria_label="Unidades",
                    class_name="registration-form-input",
                    value=AuthState.conference_unidades,
                    on_change=AuthState.set_conference_unidades,
                    **input_style,
                ),
                rx.input(
                    type="date",
                    placeholder="Validade",
                    aria_label="Validade",
                    class_name="registration-form-input conference-date-input",
                    value=AuthState.conference_validade,
                    on_change=AuthState.set_conference_validade,
                    min="0001-01-01",
                    max="9999-12-31",
                    **input_style,
                ),
                rx.button(
                    "Adicionar",
                    type="button",
                    on_click=AuthState.add_inventory,
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
        overflow="visible",
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
                value=AuthState.inventory_search,
                on_change=AuthState.set_inventory_search,
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
            rx.foreach(AuthState.filtered_inventory, inventory_card),
            width="100%",
            display="flex",
            flex_direction="column",
            gap="0.85rem",
            overflow_y="auto",
            overflow_x="visible",
            padding="0.15rem 0.35rem 0.5rem 0.15rem",
            max_height="calc(100dvh - 18rem)",
            min_height="12rem",
            scrollbar_width="none",
            class_name="inventory-product-scroll",
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
    fixed_sidebar: bool = False,
) -> rx.Component:
    return rx.hstack(
        sidebar(
            active_destination=active_destination,
            fixed_for_registration=fixed_sidebar,
        ),
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
            margin_left="16rem" if fixed_sidebar else "0",
        ),
        width="100%",
        min_height="100dvh",
        align="stretch",
        gap="0",
        background="#F7F9FC",
        position="relative",
    )


@rx.page(route="/", on_load=AuthState.require_auth)
def dashboard() -> rx.Component:
    return dashboard_layout(
        dashboard_cards(),
        active_destination="home",
        subtitle="Aqui está um resumo do seu mercado hoje.",
    )


@rx.page(route="/cadastro", on_load=AuthState.require_admin_and_load_employees)
def registration_page() -> rx.Component:
    return dashboard_layout(
        registration_panels(),
        active_destination="registration",
        subtitle="Aqui você pode adicionar funcionários novos ao sistema de gerenciamento do mercado",
        fixed_sidebar=True,
    )


@rx.page(route="/estoque", on_load=AuthState.require_admin_and_load_inventory)
def estoque_page() -> rx.Component:
    return dashboard_layout(
        inventory_panel(),
        active_destination="inventory",
        subtitle="Aqui está o estoque do mercado",
    )


@rx.page(route="/conferencia", on_load=AuthState.require_admin)
def conferencia_page() -> rx.Component:
    return dashboard_layout(
        conference_form_panel(),
        active_destination="receiving",
        subtitle="Aqui você pode adicionar produtos recém entregues pelo fornecedor ao seu estoque",
    )


@rx.page(route="/produtos", on_load=AuthState.require_admin)
def produtos_page() -> rx.Component:
    return dashboard_layout(
        product_form_panel(),
        active_destination="products",
        subtitle="Aqui você pode registrar produtos novos ao sistema do mercado",
    )


@rx.page(route="/relatorios", on_load=AuthState.require_admin)
def relatorios_page() -> rx.Component:
    return dashboard_layout(
        reports_cards(),
        active_destination="reports",
        subtitle="Aqui você pode acessar seus dashboards",
    )


@rx.page(route="/precos", on_load=AuthState.require_admin)
def precos_page() -> rx.Component:
    return dashboard_layout(
        prices_panel(),
        active_destination="prices",
        subtitle="Aqui você pode cadastrar e consultar preços dos produtos",
    )


@rx.page(route="/caixa", on_load=AuthState.require_auth)
def caixa_page() -> rx.Component:
    return cashier_page_content()


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
        ".registration-list-panel .registration-search-input, .registration-list-panel .registration-search-input:focus-within": {
            "background": "#F7F9FC !important",
            "border": "1px solid #E5E7EB !important",
            "box_shadow": "0 0 0 2px rgba(59, 130, 246, 0.2) !important",
        },
        ".registration-list-panel .registration-search-input input, .registration-list-panel .registration-search-input input:focus": {
            "background": "#F7F9FC !important",
            "color": "#000000 !important",
        },
        ".registration-list-panel .registration-search-input input::placeholder": {
            "color": "#5B6475 !important",
            "opacity": "1 !important",
        },
        ".registration-employee-scroll": {
            "scrollbar_width": "none",
            "-ms-overflow-style": "none",
        },
        ".registration-employee-scroll::-webkit-scrollbar": {
            "display": "none",
        },
        ".inventory-product-scroll": {
            "-ms-overflow-style": "none",
        },
        ".inventory-product-scroll::-webkit-scrollbar": {
            "display": "none",
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
            "width": "calc(100% - 2rem)",
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
        "@media (min-width: 760px)": {
            ".prices-fields-grid": {
                "grid_template_columns": "minmax(0, 1.5fr) minmax(10rem, 0.7fr)",
            },
            ".prices-selected-details": {
                "grid_template_columns": "minmax(0, 1.5fr) repeat(3, minmax(0, 1fr))",
            },
        },
        "@media (max-width: 639px)": {
            ".prices-search-row": {
                "flex_direction": "column",
                "align_items": "stretch",
            },
            ".prices-search-row button": {
                "width": "100%",
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
        "@media (max-width: 760px)": {
            ".cashier-shell": {
                "flex_direction": "column",
            },
            ".cashier-brand, .cashier-workspace": {
                "width": "100%",
                "min_width": "0",
            },
            ".cashier-brand": {
                "min_height": "12rem",
                "padding": "1.25rem",
            },
            ".cashier-workspace": {
                "padding_top": "0",
            },
        },
        "img": {
            "display": "block",
            "max_width": "100%",
        },
    },
)