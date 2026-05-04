with source as (
    select * from {{ source('raw', 'raw_orders') }}
),

cleaned as (
    select
        order_id,
        lower(trim(customer_email))          as customer_email,
        cast(order_timestamp as timestamp)   as order_timestamp,
        gross_amount,
        discount_amount,
        net_amount,
        channel,
        status
    from source
    where status != 'test'
)

select * from cleaned
