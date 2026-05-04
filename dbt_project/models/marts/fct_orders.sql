with orders as (
    select * from {{ ref('stg_orders') }}
),

customers as (
    select * from {{ ref('dim_customer') }}
),

dates as (
    select * from {{ ref('dim_date') }}
),

joined as (
    select
        o.order_id,
        c.customer_key,
        d.date_key,
        o.customer_email,
        o.order_timestamp,
        o.gross_amount,
        o.discount_amount,
        o.net_amount,
        o.channel,
        o.status
    from orders o

    -- SCD2-aware join: match the tier row active at order time.
    -- Guest rows (null tier dates) bypass the date range check.
    left join customers c
        on c.email = o.customer_email
        and (
            c.is_guest
            or (
                cast(o.order_timestamp as date) >= c.tier_valid_from
                and (c.tier_valid_to is null or cast(o.order_timestamp as date) <= c.tier_valid_to)
            )
        )

    left join dates d
        on d.date_key = cast(format_date('%Y%m%d', cast(o.order_timestamp as date)) as int64)
)

select * from joined
