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

Deno.test("manager can assign only operator accounts", () => {
  const manager = profile("manager-id", "manager");
  assertCanAssignRole(manager, "operator");
  for (const role of ["manager", "owner"] as const) {
    try {
      assertCanAssignRole(manager, role);
      throw new Error("Expected elevated role assignment to be rejected.");
    } catch (error) {
      if (!(error instanceof EmployeeRequestError) || error.status !== 403) {
        throw error;
      }
    }
  }
});

Deno.test("operators cannot assign employee roles", () => {
  try {
    assertCanAssignRole(profile("operator-id", "operator"), "operator");
    throw new Error("Expected operator role assignment to be rejected.");
  } catch (error) {
    if (!(error instanceof EmployeeRequestError) || error.status !== 403) {
      throw error;
    }
  }
});

Deno.test("owner can assign every supported role", () => {
  const owner = profile("owner-id", "owner");
  for (const role of ["operator", "manager", "owner"] as const) {
    assertCanAssignRole(owner, role);
  }
});

Deno.test("manager cannot edit an elevated account", () => {
  try {
    assertCanManageEmployee(
      profile("manager-id", "manager"),
      profile("owner-id", "owner"),
      "update",
    );
    throw new Error("Expected an elevated target to be rejected.");
  } catch (error) {
    if (!(error instanceof EmployeeRequestError) || error.status !== 403) {
      throw error;
    }
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
