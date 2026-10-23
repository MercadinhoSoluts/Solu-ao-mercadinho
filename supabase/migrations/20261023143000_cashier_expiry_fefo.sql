create or replace function public.complete_cashier_purchase(
    p_purchase_id uuid,
    p_payment_method text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    actor_id uuid := (select auth.uid());
    business_date date := (
        now() at time zone 'America/Sao_Paulo'
    )::date;
    purchase public.purchases;
    product_row record;
    item_row record;
    stock_row record;
    computed_total bigint;
    remaining_units bigint;
    allocated_units bigint;
begin
    if actor_id is null or public.current_app_role() is null then
        raise exception 'Not authorized' using errcode = '42501';
    end if;
    if p_payment_method is null
       or p_payment_method not in ('credit_card', 'debit_card', 'pix', 'cash') then
        raise exception 'Unsupported payment method' using errcode = '22023';
    end if;

    select * into purchase
    from public.purchases
    where id = p_purchase_id and created_by = actor_id
    for update;
    if not found then
        raise exception 'Purchase not found' using errcode = 'P1004';
    end if;

    if purchase.status = 'completed' then
        if purchase.payment_method is distinct from p_payment_method then
            raise exception 'Purchase was completed with a different payment method'
                using errcode = 'P1011';
        end if;
        return public.cashier_purchase_payload(p_purchase_id);
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

    for product_row in
        select item.product_id
        from public.purchase_items as item
        where item.purchase_id = p_purchase_id
        group by item.product_id
        order by item.product_id
    loop
        perform 1
        from public.products as product
        where product.id = product_row.product_id
        for update;
    end loop;

    for item_row in
        select item.product_id, sum(item.quantity)::bigint as quantity
        from public.purchase_items as item
        where item.purchase_id = p_purchase_id
        group by item.product_id
        order by item.product_id
    loop
        remaining_units := item_row.quantity;

        for stock_row in
            select lot.id, lot.units
            from public.stock_lots as lot
            where lot.product_id = item_row.product_id
              and lot.units > 0
              and lot.expires_on >= business_date
            order by lot.expires_on, lot.created_at, lot.id
            for update
        loop
            exit when remaining_units = 0;
            allocated_units := least(remaining_units, stock_row.units::bigint);

            update public.stock_lots
            set units = units - allocated_units::integer
            where id = stock_row.id;

            insert into public.inventory_movements (
                stock_lot_id,
                units_delta,
                movement_type,
                reason,
                created_by,
                purchase_id
            )
            values (
                stock_row.id,
                -allocated_units::integer,
                'sale',
                'Cashier sale ' || p_purchase_id::text,
                actor_id,
                p_purchase_id
            );

            remaining_units := remaining_units - allocated_units;
        end loop;

        if remaining_units > 0 then
            raise exception 'Insufficient unexpired stock for product %',
                item_row.product_id
                using errcode = 'P1010';
        end if;
    end loop;

    update public.purchases
    set status = 'completed',
        total_cents = computed_total,
        payment_method = p_payment_method,
        closed_at = now()
    where id = p_purchase_id;

    return public.cashier_purchase_payload(p_purchase_id);
end;
$$;

revoke all on function public.complete_cashier_purchase(uuid, text)
from public, anon;
grant execute on function public.complete_cashier_purchase(uuid, text)
to authenticated;
