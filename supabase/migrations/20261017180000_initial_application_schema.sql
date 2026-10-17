create type public.app_role as enum ('operator', 'manager', 'owner');

create table public.profiles (
    id uuid primary key references auth.users (id) on delete cascade,
    email text not null unique,
    name text not null check (length(btrim(name)) > 0),
    role public.app_role not null default 'operator',
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint profiles_email_normalized check (email = lower(btrim(email)))
);

create index profiles_role_idx on public.profiles (role);

create function public.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
    new.updated_at := now();
    return new;
end;
$$;

revoke all on function public.set_updated_at() from public, anon, authenticated;

create trigger profiles_set_updated_at
before update on public.profiles
for each row execute function public.set_updated_at();

create function public.sync_auth_profile()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    profile_name text;
begin
    profile_name := nullif(btrim(new.raw_user_meta_data ->> 'name'), '');
    if profile_name is null then
        profile_name := split_part(coalesce(new.email, ''), '@', 1);
    end if;
    if profile_name = '' then
        profile_name := 'Usuário';
    end if;

    insert into public.profiles (id, email, name, role, is_active)
    values (
        new.id,
        lower(btrim(new.email)),
        profile_name,
        'operator',
        (new.banned_until is null or new.banned_until < now())
    )
    on conflict (id) do update
    set email = excluded.email,
        name = excluded.name,
        is_active = excluded.is_active;

    return new;
end;
$$;

create trigger on_auth_user_created
after insert or update of email, raw_user_meta_data, banned_until
on auth.users
for each row execute function public.sync_auth_profile();

revoke all on function public.sync_auth_profile() from public, anon, authenticated;

create function public.current_app_role()
returns public.app_role
language sql
stable
security definer
set search_path = ''
as $$
    select p.role
    from public.profiles as p
    where p.id = (select auth.uid())
      and p.is_active
    limit 1;
$$;

revoke all on function public.current_app_role() from public, anon;
grant execute on function public.current_app_role() to authenticated;

create table public.products (
    id uuid primary key default gen_random_uuid(),
    product_type text not null check (length(btrim(product_type)) > 0),
    brand text not null check (length(btrim(brand)) > 0),
    weight_grams numeric(12, 3) not null check (weight_grams > 0),
    barcode text not null check (barcode = btrim(barcode) and length(barcode) > 0),
    is_active boolean not null default true,
    created_by uuid references public.profiles (id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create unique index products_barcode_unique_idx
on public.products (barcode);
create index products_name_search_idx
on public.products (lower(product_type), lower(brand));
create trigger products_set_updated_at
before update on public.products
for each row execute function public.set_updated_at();

create table public.stock_lots (
    id uuid primary key default gen_random_uuid(),
    product_id uuid not null references public.products (id),
    batch_label text not null check (length(btrim(batch_label)) > 0),
    units integer not null check (units >= 0),
    expires_on date not null,
    created_by uuid references public.profiles (id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (product_id, expires_on)
);

create index stock_lots_expiry_idx on public.stock_lots (expires_on);
create trigger stock_lots_set_updated_at
before update on public.stock_lots
for each row execute function public.set_updated_at();

create table public.inventory_movements (
    id uuid primary key default gen_random_uuid(),
    stock_lot_id uuid not null references public.stock_lots (id),
    units_delta integer not null check (units_delta <> 0),
    movement_type text not null check (movement_type in ('receipt', 'correction')),
    reason text,
    created_by uuid references public.profiles (id) on delete set null,
    created_at timestamptz not null default now()
);

create index inventory_movements_lot_created_idx
on public.inventory_movements (stock_lot_id, created_at desc);

create table public.product_price_history (
    id uuid primary key default gen_random_uuid(),
    product_id uuid not null references public.products (id),
    price_cents bigint not null check (price_cents > 0),
    created_by uuid references public.profiles (id) on delete set null,
    created_at timestamptz not null default now()
);

create index product_price_history_current_idx
on public.product_price_history (product_id, created_at desc, id desc);

create view public.current_product_prices
with (security_invoker = true)
as
select distinct on (price.product_id)
    price.product_id,
    concat_ws(
        ' ',
        product.product_type,
        product.brand,
        product.weight_grams::text || ' g'
    ) as product_name,
    product.barcode,
    product.product_type,
    product.brand,
    product.weight_grams,
    price.price_cents,
    price.created_at as price_created_at
from public.product_price_history as price
join public.products as product on product.id = price.product_id
where product.is_active
order by price.product_id, price.created_at desc, price.id desc;

alter table public.profiles enable row level security;
alter table public.products enable row level security;
alter table public.stock_lots enable row level security;
alter table public.inventory_movements enable row level security;
alter table public.product_price_history enable row level security;

revoke all on table public.profiles from anon, authenticated;
revoke all on table public.products from anon, authenticated;
revoke all on table public.stock_lots from anon, authenticated;
revoke all on table public.inventory_movements from anon, authenticated;
revoke all on table public.product_price_history from anon, authenticated;
revoke all on table public.current_product_prices from anon, authenticated;

grant select on table public.profiles to authenticated;
grant select on table public.products to authenticated;
grant insert (product_type, brand, weight_grams, barcode, created_by)
on table public.products to authenticated;
grant select on table public.stock_lots to authenticated;
grant select on table public.inventory_movements to authenticated;
grant select on table public.product_price_history to authenticated;
grant insert (product_id, price_cents, created_by)
on table public.product_price_history to authenticated;
grant select on table public.current_product_prices to authenticated;

create policy "profiles_select_self_or_admin"
on public.profiles for select to authenticated
using (
    id = (select auth.uid())
    or public.current_app_role() in ('owner', 'manager')
);

create policy "products_select_active"
on public.products for select to authenticated
using (is_active and public.current_app_role() is not null);

create policy "products_insert_by_active_user"
on public.products for insert to authenticated
with check (
    created_by = (select auth.uid())
    and public.current_app_role() in ('operator', 'manager', 'owner')
);

create policy "stock_lots_select_by_active_user"
on public.stock_lots for select to authenticated
using (public.current_app_role() is not null);

create policy "inventory_movements_select_by_active_user"
on public.inventory_movements for select to authenticated
using (public.current_app_role() is not null);

create policy "prices_select_by_admin"
on public.product_price_history for select to authenticated
using (public.current_app_role() in ('owner', 'manager'));

create policy "prices_insert_by_admin"
on public.product_price_history for insert to authenticated
with check (
    created_by = (select auth.uid())
    and public.current_app_role() in ('owner', 'manager')
);

create function public.receive_stock(
    p_product_id uuid,
    p_batch_label text,
    p_units integer,
    p_expires_on date
)
returns public.stock_lots
language plpgsql
security definer
set search_path = ''
as $$
declare
    result public.stock_lots;
    actor_id uuid := (select auth.uid());
    actor_role public.app_role := public.current_app_role();
begin
    if actor_id is null or actor_role not in ('operator', 'manager', 'owner') then
        raise exception 'Not authorized to receive stock' using errcode = '42501';
    end if;
    if p_units is null or p_units <= 0 then
        raise exception 'Units must be a positive integer' using errcode = '22023';
    end if;
    if p_expires_on is null or nullif(btrim(p_batch_label), '') is null then
        raise exception 'Batch and expiry are required' using errcode = '22023';
    end if;
    if not exists (
        select 1 from public.products
        where id = p_product_id and is_active
    ) then
        raise exception 'Active product not found' using errcode = 'P0002';
    end if;

    insert into public.stock_lots (product_id, batch_label, units, expires_on, created_by)
    values (p_product_id, btrim(p_batch_label), p_units, p_expires_on, actor_id)
    on conflict (product_id, expires_on) do update
    set units = public.stock_lots.units + excluded.units,
        updated_at = now()
    returning * into result;

    insert into public.inventory_movements (
        stock_lot_id, units_delta, movement_type, created_by
    )
    values (result.id, p_units, 'receipt', actor_id);

    return result;
end;
$$;

create function public.correct_stock(
    p_stock_lot_id uuid,
    p_units_delta integer,
    p_reason text
)
returns public.stock_lots
language plpgsql
security definer
set search_path = ''
as $$
declare
    result public.stock_lots;
    actor_id uuid := (select auth.uid());
    actor_role public.app_role := public.current_app_role();
begin
    if actor_id is null or actor_role not in ('manager', 'owner') then
        raise exception 'Not authorized to correct stock' using errcode = '42501';
    end if;
    if p_units_delta is null or p_units_delta = 0 then
        raise exception 'Correction must be non-zero' using errcode = '22023';
    end if;
    if nullif(btrim(p_reason), '') is null then
        raise exception 'Correction reason is required' using errcode = '22023';
    end if;

    update public.stock_lots
    set units = units + p_units_delta,
        updated_at = now()
    where id = p_stock_lot_id
      and units + p_units_delta >= 0
    returning * into result;

    if not found then
        raise exception 'Stock lot not found or insufficient units' using errcode = '23514';
    end if;

    insert into public.inventory_movements (
        stock_lot_id, units_delta, movement_type, reason, created_by
    )
    values (result.id, p_units_delta, 'correction', btrim(p_reason), actor_id);

    return result;
end;
$$;

revoke all on function public.receive_stock(uuid, text, integer, date) from public, anon;
revoke all on function public.correct_stock(uuid, integer, text) from public, anon;
grant execute on function public.receive_stock(uuid, text, integer, date) to authenticated;
grant execute on function public.correct_stock(uuid, integer, text) to authenticated;
