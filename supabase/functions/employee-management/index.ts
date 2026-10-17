import { createClient, type SupabaseClient } from "npm:@supabase/supabase-js@2";
import {
  assertActiveEmployee,
  assertCanAssignRole,
  assertCanManageEmployee,
  type EmployeeProfile,
  EmployeeRequestError,
  type EmployeeRole,
  isDuplicateEmailError,
  normalizeEmployeeEmail,
  parseRole,
  requireNonEmptyText,
  validateEmployeePassword,
} from "./employee_policy.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, apikey, content-type, x-client-info",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Content-Type": "application/json",
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: corsHeaders,
  });
}

function isProfile(value: unknown): value is EmployeeProfile {
  if (!value || typeof value !== "object") {
    return false;
  }
  const profile = value as Partial<EmployeeProfile>;
  return (
    typeof profile.id === "string" &&
    typeof profile.name === "string" &&
    typeof profile.email === "string" &&
    (profile.role === "owner" ||
      profile.role === "manager" ||
      profile.role === "operator") &&
    typeof profile.is_active === "boolean"
  );
}

function authErrorResponse(error: {
  code?: string;
  message?: string;
  status?: number;
}): EmployeeRequestError {
  if (isDuplicateEmailError(error)) {
    return new EmployeeRequestError(409, "Este e-mail já está cadastrado.");
  }
  if (error.status === 422) {
    return new EmployeeRequestError(
      400,
      "Verifique os dados informados e tente novamente.",
    );
  }
  return new EmployeeRequestError(
    502,
    "Não foi possível concluir a operação de funcionário.",
  );
}

function requireBearerToken(request: Request): string {
  const authorization = request.headers.get("authorization") ?? "";
  const match = /^Bearer\s+(\S+)$/i.exec(authorization);
  if (!match) {
    throw new EmployeeRequestError(401, "Sessão inválida ou expirada.");
  }
  return match[1];
}

async function loadProfile(
  adminClient: SupabaseClient,
  userId: string,
): Promise<EmployeeProfile> {
  const { data, error } = await adminClient
    .from("profiles")
    .select("id, name, email, role, is_active")
    .eq("id", userId)
    .maybeSingle();

  if (error) {
    throw new EmployeeRequestError(
      500,
      "Não foi possível consultar o perfil do funcionário.",
    );
  }
  if (!isProfile(data)) {
    throw new EmployeeRequestError(403, "Perfil não autorizado.");
  }
  return data;
}

async function handleRequest(request: Request): Promise<Response> {
  if (request.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }
  if (request.method !== "POST") {
    throw new EmployeeRequestError(405, "Método não permitido.");
  }

  const url = Deno.env.get("SUPABASE_URL");
  const anonKey = Deno.env.get("SUPABASE_ANON_KEY");
  const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !anonKey || !serviceRoleKey) {
    throw new EmployeeRequestError(
      500,
      "A configuração segura do serviço de funcionários está incompleta.",
    );
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch (error) {
    if (error instanceof SyntaxError) {
      throw new EmployeeRequestError(400, "O corpo da solicitação é inválido.");
    }
    throw error;
  }
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    throw new EmployeeRequestError(400, "O corpo da solicitação é inválido.");
  }
  const payload = body as Record<string, unknown>;

  const accessToken = requireBearerToken(request);
  const authClient = createClient(url, anonKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  });
  const { data: authData, error: authError } = await authClient.auth.getUser(
    accessToken,
  );
  if (authError || !authData.user) {
    throw new EmployeeRequestError(401, "Sessão inválida ou expirada.");
  }

  const adminClient = createClient(url, serviceRoleKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  });
  const actor = await loadProfile(adminClient, authData.user.id);
  assertActiveEmployee(actor);

  const action = requireNonEmptyText(payload.action, "uma ação válida");
  if (action === "list") {
    if (actor.role !== "owner" && actor.role !== "manager") {
      throw new EmployeeRequestError(
        403,
        "Você não pode consultar funcionários.",
      );
    }
    const { data, error } = await adminClient
      .from("profiles")
      .select("id, name, email, role, is_active, created_at")
      .order("name", { ascending: true });
    if (error) {
      throw new EmployeeRequestError(
        500,
        "Não foi possível consultar os funcionários.",
      );
    }
    return jsonResponse({ employees: data });
  }

  if (action === "create") {
    const name = requireNonEmptyText(payload.name, "um nome");
    const email = normalizeEmployeeEmail(payload.email);
    const password = validateEmployeePassword(payload.password);
    const role = parseRole(payload.role);
    assertCanAssignRole(actor, role);

    const { data, error } = await adminClient.auth.admin.createUser({
      email,
      password,
      email_confirm: true,
      user_metadata: { name },
    });
    if (error || !data.user) {
      throw authErrorResponse(error ?? {});
    }

    const { data: createdProfile, error: profileError } = await adminClient
      .from("profiles")
      .update({ role })
      .eq("id", data.user.id)
      .select("id")
      .maybeSingle();
    if (profileError || !createdProfile) {
      const { error: cleanupError } = await adminClient.auth.admin.deleteUser(
        data.user.id,
      );
      if (cleanupError) {
        throw new EmployeeRequestError(
          500,
          "O perfil não foi concluído e requer revisão de um administrador.",
        );
      }
      throw new EmployeeRequestError(
        500,
        "Não foi possível concluir o cadastro do funcionário.",
      );
    }
    return jsonResponse({
      employee: {
        id: data.user.id,
        name,
        email,
        role,
        is_active: true,
      },
    }, 201);
  }

  if (action === "update") {
    const userId = requireNonEmptyText(payload.userId, "um funcionário");
    if (!/^[0-9a-f-]{36}$/i.test(userId)) {
      throw new EmployeeRequestError(
        400,
        "O funcionário informado é inválido.",
      );
    }
    const target = await loadProfile(adminClient, userId);
    assertCanManageEmployee(actor, target, "update");
    const name = requireNonEmptyText(payload.name, "um nome");
    const email = normalizeEmployeeEmail(payload.email);
    const role = parseRole(payload.role);
    assertCanAssignRole(actor, role);
    const password =
      typeof payload.password === "string" && payload.password.length > 0
        ? validateEmployeePassword(payload.password)
        : undefined;

    const roleChanged = role !== target.role;
    if (roleChanged) {
      const { data: updatedProfile, error: profileError } = await adminClient
        .from("profiles")
        .update({ role })
        .eq("id", userId)
        .eq("role", target.role)
        .select("id")
        .maybeSingle();
      if (profileError || !updatedProfile) {
        throw new EmployeeRequestError(
          409,
          "O funcionário foi alterado. Atualize a lista e tente novamente.",
        );
      }
    }

    let authUpdate: Awaited<
      ReturnType<typeof adminClient.auth.admin.updateUserById>
    >;
    try {
      authUpdate = await adminClient.auth.admin.updateUserById(userId, {
        email,
        user_metadata: { name },
        ...(password ? { password } : {}),
      });
    } catch (error) {
      if (roleChanged) {
        const { data: restoredProfile, error: restoreError } = await adminClient
          .from("profiles")
          .update({ role: target.role })
          .eq("id", userId)
          .eq("role", role)
          .select("id")
          .maybeSingle();
        if (restoreError || !restoredProfile) {
          throw new EmployeeRequestError(
            500,
            "A atualização falhou e o cargo exige revisão de um administrador.",
          );
        }
      }
      console.error(
        "employee-management auth update failed",
        error instanceof Error ? error.name : "unknown error",
      );
      throw new EmployeeRequestError(
        502,
        "Não foi possível atualizar o funcionário.",
      );
    }
    if (authUpdate.error) {
      if (roleChanged) {
        const { data: restoredProfile, error: restoreError } = await adminClient
          .from("profiles")
          .update({ role: target.role })
          .eq("id", userId)
          .eq("role", role)
          .select("id")
          .maybeSingle();
        if (restoreError || !restoredProfile) {
          throw new EmployeeRequestError(
            500,
            "A atualização falhou e o cargo exige revisão de um administrador.",
          );
        }
      }
      throw authErrorResponse(authUpdate.error);
    }

    return jsonResponse({
      employee: {
        id: userId,
        name,
        email,
        role,
        is_active: target.is_active,
      },
    });
  }

  if (action === "delete") {
    const userId = requireNonEmptyText(payload.userId, "um funcionário");
    if (!/^[0-9a-f-]{36}$/i.test(userId)) {
      throw new EmployeeRequestError(
        400,
        "O funcionário informado é inválido.",
      );
    }
    const target = await loadProfile(adminClient, userId);
    assertCanManageEmployee(actor, target, "delete");
    const { error } = await adminClient.auth.admin.deleteUser(userId);
    if (error) {
      throw new EmployeeRequestError(
        502,
        "Não foi possível excluir o funcionário.",
      );
    }
    return jsonResponse({ deleted: true, userId });
  }

  throw new EmployeeRequestError(400, "A ação solicitada não é suportada.");
}

Deno.serve(async (request: Request) => {
  try {
    return await handleRequest(request);
  } catch (error) {
    if (error instanceof EmployeeRequestError) {
      return jsonResponse({ error: error.message }, error.status);
    }
    console.error(
      "employee-management request failed",
      error instanceof Error ? error.name : "unknown error",
    );
    return jsonResponse(
      { error: "Não foi possível concluir a solicitação." },
      500,
    );
  }
});
