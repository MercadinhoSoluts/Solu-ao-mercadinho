create table public.purchases (
    id uuid primary key default gen_random_uuid(),
    created_by uuid references public.profiles (id) on delete set null,
    status text not null default 'open'
        check (status in ('open', 'completed', 'cancelled')),
    total_cents bigint not null default 0 check (total_cents >= 0),
    created_at timestamptz not null default now(),
    closed_at timestamptz,
    check (
        (status = 'open' and closed_at is null)
        or (status in ('completed', 'cancelled') and closed_at is not null)
    )
);

create index purchases_created_by_status_idx
on public.purchases (created_by, status, created_at desc);

create unique index purchases_one_open_per_user_idx
on public.purchases (created_by)
where status = 'open' and created_by is not null;

create table public.purchase_open_requests (
    request_id uuid primary key,
    purchase_id uuid not null references public.purchases (id),
    created_by uuid references public.profiles (id) on delete set null,
    created_at timestamptz not null default now()
);

create table public.purchase_items (
    id uuid primary key default gen_random_uuid(),
    purchase_id uuid not null references public.purchases (id),
    product_id uuid not null references public.products (id),
    product_name text not null check (length(btrim(product_name)) > 0),
    barcode text not null check (length(btrim(barcode)) > 0),
    quantity integer not null check (quantity > 0),
    unit_price_cents bigint not null check (unit_price_cents > 0),
    line_total_cents bigint not null check (
        line_total_cents = quantity::bigint * unit_price_cents
    ),
    created_at timestamptz not null default now(),
    unique (purchase_id, product_id, unit_price_cents)
);

create index purchase_items_purchase_idx
on public.purchase_items (purchase_id, created_at, id);

create table public.purchase_item_requests (
    request_id uuid primary key,
    purchase_id uuid not null references public.purchases (id),
    barcode text not null,
    quantity integer not null check (quantity > 0),
    created_at timestamptz not null default now()
);

alter table public.purchases enable row level security;
alter table public.purchase_items enable row level security;
alter table public.purchase_open_requests enable row level security;
alter table public.purchase_item_requests enable row level security;

revoke all on table public.purchases from anon, authenticated;
revoke all on table public.purchase_items from anon, authenticated;
revoke all on table public.purchase_open_requests from anon, authenticated;
revoke all on table public.purchase_item_requests from anon, authenticated;

grant select on table public.purchases, public.purchase_items to authenticated;

create policy "purchases_select_own"
on public.purchases for select to authenticated
using (created_by = (select auth.uid()));

create policy "purchase_items_select_own"
on public.purchase_items for select to authenticated
using (
    exists (
        select 1
        from public.purchases as purchase
        where purchase.id = purchase_items.purchase_id
          and purchase.created_by = (select auth.uid())
    )
);

create function public.cashier_purchase_payload(p_purchase_id uuid)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
    select to_jsonb(purchase) || jsonb_build_object(
        'items',
        coalesce(
            (
                select jsonb_agg(to_jsonb(item) order by item.created_at, item.id)
                from public.purchase_items as item
                where item.purchase_id = purchase.id
            ),
            '[]'::jsonb
        )
    )
    from public.purchases as purchase
    where purchase.id = p_purchase_id;
$$;

create function public.open_cashier_purchase(p_open_request_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    actor_id uuid := (select auth.uid());
    purchase_id uuid;
    request_purchase_id uuid;
    request_owner_id uuid;
begin
    if actor_id is null or public.current_app_role() is null then
        raise exception 'Not authorized' using errcode = '42501';
    end if;
    if p_open_request_id is null then
        raise exception 'Opening request is required' using errcode = '22023';
    end if;

    perform 1
    from public.profiles as profile
    where profile.id = actor_id
    for update;

    select request.purchase_id, request.created_by
    into request_purchase_id, request_owner_id
    from public.purchase_open_requests as request
    where request.request_id = p_open_request_id;
    if found then
        if request_owner_id is distinct from actor_id then
            raise exception 'Opening request belongs to another user'
                using errcode = '42501';
        end if;
        return public.cashier_purchase_payload(request_purchase_id);
    end if;

    select id into purchase_id
    from public.purchases
    where created_by = actor_id and status = 'open'
    for update;
    if purchase_id is null then
        insert into public.purchases (created_by)
        values (actor_id)
        on conflict (created_by)
        where status = 'open' and created_by is not null
        do nothing
        returning id into purchase_id;

        if purchase_id is null then
            select id into purchase_id
            from public.purchases
            where created_by = actor_id and status = 'open';
            if purchase_id is null then
                raise exception 'Could not create purchase' using errcode = 'P1008';
            end if;
        end if;
    end if;

    insert into public.purchase_open_requests (
        request_id, purchase_id, created_by
    )
    values (p_open_request_id, purchase_id, actor_id)
    on conflict (request_id) do nothing;

    select request.purchase_id, request.created_by
    into request_purchase_id, request_owner_id
    from public.purchase_open_requests as request
    where request.request_id = p_open_request_id;
    if request_owner_id is distinct from actor_id then
        raise exception 'Opening request belongs to another user'
            using errcode = '42501';
    end if;

    return public.cashier_purchase_payload(request_purchase_id);
end;
$$;

create function public.get_cashier_purchase(p_purchase_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    actor_id uuid := (select auth.uid());
    purchase public.purchases;
begin
    if actor_id is null or public.current_app_role() is null then
        raise exception 'Not authorized' using errcode = '42501';
    end if;

    select * into purchase
    from public.purchases
    where id = p_purchase_id and created_by = actor_id;
    if not found then
        raise exception 'Purchase not found' using errcode = 'P1004';
    end if;

    return public.cashier_purchase_payload(purchase.id);
end;
$$;

create function public.add_cashier_purchase_item(
    p_purchase_id uuid,
    p_barcode text,
    p_quantity integer,
    p_request_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    actor_id uuid := (select auth.uid());
    purchase public.purchases;
    previous_request public.purchase_item_requests;
    product public.products;
    applied_price_cents bigint;
    item_name text;
begin
    if actor_id is null or public.current_app_role() is null then
        raise exception 'Not authorized' using errcode = '42501';
    end if;
    if p_quantity is null or p_quantity <= 0 then
        raise exception 'Quantity must be a positive integer' using errcode = 'P1006';
    end if;
    if p_request_id is null or nullif(btrim(p_barcode), '') is null then
        raise exception 'Barcode and request id are required' using errcode = '22023';
    end if;

    select * into previous_request
    from public.purchase_item_requests
    where request_id = p_request_id;
    if found then
        if previous_request.purchase_id <> p_purchase_id
           or previous_request.barcode <> btrim(p_barcode)
           or previous_request.quantity <> p_quantity then
            raise exception 'Request id was already used with different data'
                using errcode = 'P1007';
        end if;
        select * into purchase
        from public.purchases
        where id = p_purchase_id and created_by = actor_id;
        if not found then
            raise exception 'Purchase not found' using errcode = 'P1004';
        end if;
        return public.cashier_purchase_payload(purchase.id);
    end if;

    select * into purchase
    from public.purchases
    where id = p_purchase_id and created_by = actor_id
    for update;
    if not found then
        raise exception 'Purchase not found' using errcode = 'P1004';
    end if;
    if purchase.status <> 'open' then
        raise exception 'Purchase is not open' using errcode = 'P1003';
    end if;

    select * into product
    from public.products
    where barcode = btrim(p_barcode) and is_active;
    if not found then
        raise exception 'Product not found' using errcode = 'P1001';
    end if;

    select price.price_cents into applied_price_cents
    from public.product_price_history as price
    where price.product_id = product.id
    order by price.created_at desc, price.id desc
    limit 1;
    if applied_price_cents is null or applied_price_cents <= 0 then
        raise exception 'Product has no current price' using errcode = 'P1002';
    end if;

    item_name := concat_ws(
        ' ',
        product.product_type,
        product.brand,
        pg_catalog.trim_scale(product.weight_grams)::text || ' g'
    );

    insert into public.purchase_item_requests (
        request_id, purchase_id, barcode, quantity
    )
    values (p_request_id, p_purchase_id, btrim(p_barcode), p_quantity)
    on conflict (request_id) do nothing;

    if not found then
        select * into previous_request
        from public.purchase_item_requests
        where request_id = p_request_id;
        if previous_request.purchase_id <> p_purchase_id
           or previous_request.barcode <> btrim(p_barcode)
           or previous_request.quantity <> p_quantity then
            raise exception 'Request id was already used with different data'
                using errcode = 'P1007';
        end if;
        return public.cashier_purchase_payload(p_purchase_id);
    end if;

    insert into public.purchase_items (
        purchase_id,
        product_id,
        product_name,
        barcode,
        quantity,
        unit_price_cents,
        line_total_cents
    )
    values (
        p_purchase_id,
        product.id,
        item_name,
        product.barcode,
        p_quantity,
        applied_price_cents,
        p_quantity::bigint * applied_price_cents
    )
    on conflict (purchase_id, product_id, unit_price_cents)
    do update set
        quantity = public.purchase_items.quantity + excluded.quantity,
        line_total_cents = (
            public.purchase_items.quantity + excluded.quantity
        )::bigint * public.purchase_items.unit_price_cents;

    update public.purchases
    set total_cents = (
        select coalesce(sum(item.line_total_cents), 0)
        from public.purchase_items as item
        where item.purchase_id = p_purchase_id
    )
    where id = p_purchase_id;

    return public.cashier_purchase_payload(p_purchase_id);
end;
$$;

create function public.complete_cashier_purchase(p_purchase_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    actor_id uuid := (select auth.uid());
    purchase public.purchases;
    computed_total bigint;
begin
    if actor_id is null or public.current_app_role() is null then
        raise exception 'Not authorized' using errcode = '42501';
    end if;

    select * into purchase
    from public.purchases
    where id = p_purchase_id and created_by = actor_id
    for update;
    if not found then
        raise exception 'Purchase not found' using errcode = 'P1004';
    end if;
    if purchase.status <> 'open' then
        raise exception 'Purchase is not open' using errcode = 'P1003';
    end if;

    select coalesce(sum(item.line_total_cents), 0) into computed_total
    from public.purchase_items as item
    where item.purchase_id = p_purchase_id;
    if computed_total <= 0 then
        raise exception 'Purchase has no items' using errcode = 'P1005';
    end if;

    update public.purchases
    set status = 'completed',
        total_cents = computed_total,
        closed_at = now()
    where id = p_purchase_id;

    return public.cashier_purchase_payload(p_purchase_id);
end;
$$;

create function public.cancel_cashier_purchase(p_purchase_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    actor_id uuid := (select auth.uid());
    purchase public.purchases;
begin
    if actor_id is null or public.current_app_role() is null then
        raise exception 'Not authorized' using errcode = '42501';
    end if;

    select * into purchase
    from public.purchases
    where id = p_purchase_id and created_by = actor_id
    for update;
    if not found then
        raise exception 'Purchase not found' using errcode = 'P1004';
    end if;
    if purchase.status <> 'open' then
        raise exception 'Purchase is not open' using errcode = 'P1003';
    end if;

    update public.purchases
    set status = 'cancelled',
        closed_at = now()
    where id = p_purchase_id;

    return public.cashier_purchase_payload(p_purchase_id);
end;
$$;

revoke all on function public.cashier_purchase_payload(uuid) from public, anon, authenticated;
revoke all on function public.open_cashier_purchase(uuid) from public, anon;
revoke all on function public.get_cashier_purchase(uuid) from public, anon;
revoke all on function public.add_cashier_purchase_item(uuid, text, integer, uuid) from public, anon;
revoke all on function public.complete_cashier_purchase(uuid) from public, anon;
revoke all on function public.cancel_cashier_purchase(uuid) from public, anon;

grant execute on function public.open_cashier_purchase(uuid) to authenticated;
grant execute on function public.get_cashier_purchase(uuid) to authenticated;
grant execute on function public.add_cashier_purchase_item(uuid, text, integer, uuid) to authenticated;
grant execute on function public.complete_cashier_purchase(uuid) to authenticated;
grant execute on function public.cancel_cashier_purchase(uuid) to authenticated;
