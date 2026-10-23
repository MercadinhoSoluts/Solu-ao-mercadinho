-- Business role names are aliases for the legacy enum values already in use.
CREATE OR REPLACE FUNCTION public.normalize_app_role(raw_role text)
RETURNS public.app_role
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT CASE lower(btrim(raw_role))
        WHEN 'proprietario' THEN 'owner'::public.app_role
        WHEN 'proprietário' THEN 'owner'::public.app_role
        WHEN 'owner' THEN 'owner'::public.app_role
        WHEN 'admin' THEN 'manager'::public.app_role
        WHEN 'administrador' THEN 'manager'::public.app_role
        WHEN 'manager' THEN 'manager'::public.app_role
        WHEN 'caixa' THEN 'operator'::public.app_role
        WHEN 'operator' THEN 'operator'::public.app_role
        ELSE NULL::public.app_role
    END;
$$;

REVOKE ALL ON FUNCTION public.normalize_app_role(text) FROM public, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.normalize_app_role(text) TO authenticated;
