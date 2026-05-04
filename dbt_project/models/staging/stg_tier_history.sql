with source as (
    select * from {{ source('raw', 'raw_tier_history') }}
),

renamed as (
    select
        trim(crm_id)             as crm_id,
        tier,
        cast(valid_from as date) as valid_from
    from source
)

select * from renamed
