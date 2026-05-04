with orders as (
    select * from {{ ref('fct_orders') }}
    where status != 'refunded'
),

customers as (
    select * from {{ ref('dim_customer') }}
),

dates as (
    select * from {{ ref('dim_date') }}
),

joined as (
    select
        d.date_day,
        c.acquisition_channel,
        c.region,
        o.net_amount,
        o.order_id,
        o.customer_key
    from orders o
    left join customers c on o.customer_key = c.customer_key
    left join dates d on o.date_key = d.date_key
),

aggregated as (
    select
        date_day,
        acquisition_channel,
        region,
        sum(net_amount)               as net_revenue,
        count(order_id)               as order_count,
        count(distinct customer_key)  as customer_count
    from joined
    group by 1, 2, 3
)

select * from aggregated
