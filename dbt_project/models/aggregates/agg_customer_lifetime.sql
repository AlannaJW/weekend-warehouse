-- This aggregate uses is_current = true to snapshot each customer's state RIGHT NOW.
-- It is NOT a point-in-time model — joining it to historical orders will return the
-- customer's current tier/region, not the values active at order time. For
-- point-in-time queries use dim_customer directly with the BETWEEN convention.

with current_customers as (
    select * from {{ ref('dim_customer') }}
    where is_current = true
),

-- Aggregate by email directly to capture all orders regardless of which tier period
-- the customer was in at order time. Avoids the SCD2 date-range join problem in fct_orders
-- where orders pre-dating tier_valid_from resolve to a null customer_key.
order_metrics as (
    select
        customer_email,
        min(cast(order_timestamp as date))  as first_order_date,
        max(cast(order_timestamp as date))  as most_recent_order_date,
        count(order_id)                     as lifetime_order_count,
        sum(net_amount)                     as lifetime_net_revenue
    from {{ ref('fct_orders') }}
    where status != 'refunded'
    group by 1
),

joined as (
    select
        c.customer_key,
        c.crm_id,
        c.is_guest,
        c.tier                                                        as current_tier,
        c.region,
        c.acquisition_channel,
        m.first_order_date,
        m.most_recent_order_date,
        date_diff(current_date(), m.most_recent_order_date, day)      as days_since_last_order,
        coalesce(m.lifetime_order_count, 0)                           as lifetime_order_count,
        coalesce(m.lifetime_net_revenue, 0)                           as lifetime_net_revenue,
        safe_divide(m.lifetime_net_revenue, m.lifetime_order_count)   as average_order_value
    from current_customers c
    left join order_metrics m on c.email = m.customer_email
)

select * from joined
