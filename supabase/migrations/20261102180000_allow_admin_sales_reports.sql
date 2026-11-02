create policy "purchases_select_for_admin_reports"
on public.purchases for select to authenticated
using (
    public.current_app_role() in (
        'owner'::public.app_role,
        'manager'::public.app_role
    )
);
