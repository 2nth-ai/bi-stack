with source as (
    select * from {{ ref('clients') }}
)

select
    client_id,
    name as client_name,
    segment,
    region,
    credit_limit_zar
from source
