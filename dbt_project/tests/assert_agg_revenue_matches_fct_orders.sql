-- Asserts that the total net_revenue in agg_revenue_daily matches the sum of
-- net_amount in fct_orders for non-refunded orders. Returns rows on failure.

with agg_total as (
    select sum(net_revenue) as total
    from {{ ref('agg_revenue_daily') }}
),

fct_total as (
    select sum(net_amount) as total
    from {{ ref('fct_orders') }}
    where status != 'refunded'
),

comparison as (
    select
        agg_total.total  as agg_net_revenue,
        fct_total.total  as fct_net_amount,
        abs(agg_total.total - fct_total.total) as difference
    from agg_total
    cross join fct_total
)

select * from comparison
where difference > 0.01
