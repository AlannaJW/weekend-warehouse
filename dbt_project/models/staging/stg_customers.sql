with source as (
    select * from {{ source('raw', 'raw_customers') }}
),

renamed as (
    select
        crm_id,
        lower(trim(email))       as email,
        full_name,
        cast(signup_date as date) as signup_date,
        region,
        acquisition_channel
    from source
)

select * from renamed
