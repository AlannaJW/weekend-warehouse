with source as (
    select * from {{ source('raw', 'raw_web_events') }}
),

cleaned as (
    select
        event_id,
        anonymous_id,
        nullif(lower(trim(customer_email)), '') as customer_email,
        event_type,
        cast(event_timestamp as timestamp)      as event_timestamp,
        session_id,
        page_url
    from source
)

select * from cleaned
