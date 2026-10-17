export const SUPPORTED_ROLES = ["owner", "manager", "operator"] as const;

export type EmployeeRole = (typeof SUPPORTED_ROLES)[number];
export type EmployeeOperation = "update" | "delete";

export interface EmployeeProfile {
  id: string;
  name: string;
  email: string;
  role: EmployeeRole;
  is_active: boolean;
}

export class EmployeeRequestError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

export function assertActiveEmployee(actor: EmployeeProfile): void {
  if (!actor.is_active) {
    throw new EmployeeRequestError(403, "Perfil inativo.");
  }
}

export function isDuplicateEmailError(error: {
  code?: string;
  message?: string;
}): boolean {
  const normalizedMessage = error.message?.toLowerCase() ?? "";
  return (
    error.code === "email_exists" ||
    normalizedMessage.includes("already registered") ||
    normalizedMessage.includes("already been registered")
  );
}

export function parseRole(value: unknown): EmployeeRole {
  if (
    typeof value !== "string" ||
    !SUPPORTED_ROLES.includes(value as EmployeeRole)
  ) {
    throw new EmployeeRequestError(400, "O cargo informado é inválido.");
  }
  return value as EmployeeRole;
}

export function normalizeEmployeeEmail(value: unknown): string {
  if (typeof value !== "string") {
    throw new EmployeeRequestError(400, "Informe um e-mail válido.");
  }

  const email = value.trim().toLowerCase();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    throw new EmployeeRequestError(400, "Informe um e-mail válido.");
  }
  return email;
}

export function validateEmployeePassword(value: unknown): string {
  if (
    typeof value !== "string" ||
    value.length < 12 ||
    !/[A-Z]/.test(value) ||
    !/[a-z]/.test(value) ||
    !/[0-9]/.test(value) ||
    !/[^A-Za-z0-9]/.test(value)
  ) {
    throw new EmployeeRequestError(
      400,
      "A senha deve ter pelo menos 12 caracteres e incluir maiúscula, minúscula, número e símbolo.",
    );
  }
  return value;
}

export function assertCanAssignRole(
  actor: EmployeeProfile,
  role: EmployeeRole,
): void {
  if (actor.role !== "owner" && actor.role !== "manager") {
    throw new EmployeeRequestError(
      403,
      "Você não pode gerenciar funcionários.",
    );
  }
  if (actor.role === "manager" && role !== "operator") {
    throw new EmployeeRequestError(
      403,
      "Gerentes podem gerenciar somente funcionários operadores.",
    );
  }
}

export function assertCanManageEmployee(
  actor: EmployeeProfile,
  target: EmployeeProfile,
  operation: EmployeeOperation,
): void {
  if (actor.role !== "owner" && actor.role !== "manager") {
    throw new EmployeeRequestError(
      403,
      "Você não pode gerenciar funcionários.",
    );
  }
  if (actor.role === "manager" && target.role !== "operator") {
    throw new EmployeeRequestError(
      403,
      "Gerentes podem gerenciar somente funcionários operadores.",
    );
  }
  if (operation === "delete" && actor.id === target.id) {
    throw new EmployeeRequestError(
      403,
      "Não é possível excluir a própria conta por esta tela.",
    );
  }
}

export function requireNonEmptyText(
  value: unknown,
  fieldName: string,
): string {
  if (typeof value !== "string" || !value.trim()) {
    throw new EmployeeRequestError(400, `Informe ${fieldName}.`);
  }
  return value.trim();
}
