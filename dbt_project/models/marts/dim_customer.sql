-- This model uses the inclusive interval convention: each row's [valid_from, valid_to]
-- represents the period the row is active, with valid_to one day before the next
-- row's valid_from. Point-in-time joins should use:
--    join dim_customer on order_date BETWEEN valid_from AND valid_to

with customers as (
    select * from {{ ref('stg_customers') }}
),

tier_history as (
    select * from {{ ref('stg_tier_history') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
),

-- Derive valid_to and is_current from the next tier row per customer
tier_scd2 as (
    select
        crm_id,
        tier,
        valid_from,
        date_sub(
            lead(valid_from) over (partition by crm_id order by valid_from),
            interval 1 day
        )                                                                         as valid_to,
        lead(valid_from) over (partition by crm_id order by valid_from) is null   as is_current
    from tier_history
),

-- One row per CRM customer per tier period
crm_customers as (
    select
        {{ dbt_utils.generate_surrogate_key(['c.crm_id', 'th.valid_from']) }}  as customer_key,
        c.crm_id,
        c.email,
        c.full_name,
        c.signup_date,
        c.region,
        c.acquisition_channel,
        th.tier,
        th.valid_from  as tier_valid_from,
        th.valid_to    as tier_valid_to,
        th.is_current,
        false          as is_guest
    from customers c
    inner join tier_scd2 th on c.crm_id = th.crm_id
),

-- Emails that appear in orders but have no CRM record
guest_emails as (
    select distinct lower(trim(customer_email)) as email
    from orders
    where customer_email is not null
      and lower(trim(customer_email)) not in (select email from customers)
),

-- Synthetic guest rows so fct_orders always has a valid FK
guest_customers as (
    select
        {{ dbt_utils.generate_surrogate_key(['email']) }}  as customer_key,
        cast(null as string)  as crm_id,
        email,
        cast(null as string)  as full_name,
        cast(null as date)    as signup_date,
        cast(null as string)  as region,
        cast(null as string)  as acquisition_channel,
        cast(null as string)  as tier,
        cast(null as date)    as tier_valid_from,
        cast(null as date)    as tier_valid_to,
        true                  as is_current,
        true                  as is_guest
    from guest_emails
)

select * from crm_customers
union all
select * from guest_customers
