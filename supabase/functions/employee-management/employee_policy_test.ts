import {
  assertActiveEmployee,
  assertCanAssignRole,
  assertCanManageEmployee,
  type EmployeeProfile,
  EmployeeRequestError,
  isDuplicateEmailError,
  normalizeEmployeeEmail,
  parseRole,
  validateEmployeePassword,
} from "./employee_policy.ts";

function profile(
  id: string,
  role: EmployeeProfile["role"],
): EmployeeProfile {
  return {
    id,
    name: "Test User",
    email: "test@example.invalid",
    role,
    is_active: true,
  };
}

Deno.test("manager and owner have identical role assignment permissions", () => {
  const manager = profile("admin-id", parseRole("admin"));
  const owner = profile("owner-id", parseRole("proprietario"));
  for (const role of ["operator", "manager", "owner"] as const) {
    assertCanAssignRole(manager, role);
    assertCanAssignRole(owner, role);
  }
});

Deno.test("business role aliases map to the existing enum values", () => {
  const aliases = [
    ["proprietario", "owner"],
    ["admin", "manager"],
    ["caixa", "operator"],
  ] as const;
  for (const [alias, expectedRole] of aliases) {
    if (parseRole(alias) !== expectedRole) {
      throw new Error(`Expected ${alias} to map to ${expectedRole}.`);
    }
  }
});

Deno.test("cashier cannot assign roles or manage employee accounts", () => {
  const cashier = profile("cashier-id", parseRole("caixa"));
  const target = profile("manager-id", "manager");
  for (const role of ["operator", "manager", "owner"] as const) {
    try {
      assertCanAssignRole(cashier, role);
      throw new Error("Expected cashier role assignment to be rejected.");
    } catch (error) {
      if (!(error instanceof EmployeeRequestError) || error.status !== 403) {
        throw error;
      }
    }
  }
  for (const operation of ["update", "delete"] as const) {
    try {
      assertCanManageEmployee(cashier, target, operation);
      throw new Error(`Expected cashier ${operation} to be rejected.`);
    } catch (error) {
      if (!(error instanceof EmployeeRequestError) || error.status !== 403) {
        throw error;
      }
    }
  }
});

Deno.test("manager and owner can manage the same target roles", () => {
  const manager = profile("admin-id", parseRole("admin"));
  const owner = profile("owner-id", parseRole("proprietario"));
  for (const targetRole of ["operator", "manager", "owner"] as const) {
    assertCanManageEmployee(
      manager,
      profile(`target-${targetRole}`, targetRole),
      "update",
    );
    assertCanManageEmployee(
      owner,
      profile(`target-${targetRole}`, targetRole),
      "update",
    );
  }
});

Deno.test("owner cannot delete their own account", () => {
  const owner = profile("owner-id", "owner");
  try {
    assertCanManageEmployee(owner, owner, "delete");
    throw new Error("Expected self-deletion to be rejected.");
  } catch (error) {
    if (!(error instanceof EmployeeRequestError) || error.status !== 403) {
      throw error;
    }
  }
});

Deno.test("owner can delete another account", () => {
  assertCanManageEmployee(
    profile("owner-id", "owner"),
    profile("operator-id", "operator"),
    "delete",
  );
});

Deno.test("inactive actors cannot manage employees", () => {
  try {
    assertActiveEmployee({ ...profile("owner-id", "owner"), is_active: false });
    throw new Error("Expected an inactive actor to be rejected.");
  } catch (error) {
    if (!(error instanceof EmployeeRequestError) || error.status !== 403) {
      throw error;
    }
  }
});

Deno.test("email is normalized before Auth operations", () => {
  if (normalizeEmployeeEmail("  ANA@EXAMPLE.COM ") !== "ana@example.com") {
    throw new Error("Email normalization failed.");
  }
});

Deno.test("duplicate Auth email errors are recognized without exposing details", () => {
  if (!isDuplicateEmailError({ code: "email_exists" })) {
    throw new Error("The Auth duplicate-email code was not recognized.");
  }
  if (!isDuplicateEmailError({ message: "User already registered" })) {
    throw new Error("The Auth duplicate-email message was not recognized.");
  }
  if (isDuplicateEmailError({ message: "User not found" })) {
    throw new Error("An unrelated Auth error was misclassified.");
  }
});

Deno.test("password policy matches the existing account requirement", () => {
  validateEmployeePassword("SenhaSegura123!");
  try {
    validateEmployeePassword("short");
    throw new Error("Expected a weak password to be rejected.");
  } catch (error) {
    if (!(error instanceof EmployeeRequestError) || error.status !== 400) {
      throw error;
    }
  }
});

Deno.test("unsupported employee role is rejected", () => {
  try {
    parseRole("administrator");
    throw new Error("Expected an unsupported role to be rejected.");
  } catch (error) {
    if (!(error instanceof EmployeeRequestError) || error.status !== 400) {
      throw error;
    }
  }
});
