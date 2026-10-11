with base as (

    select
        id,
        class,
        probability_benign,
        probability_ddos,
        created_at
    from {{ ref('stg_predictions') }}

),

ordered as (

    select
        *,
        row_number() over (
            order by created_at
        ) as prediction_sequence,

        count(*) over () as total_predictions,

        sum(
            case
                when class = 'DDoS' then 1
                else 0
            end
        ) over () as total_ddos,

        sum(
            case
                when class = 'BENIGN' then 1
                else 0
            end
        ) over () as total_benign

    from base

),

final as (

    select
        id,
        class,
        probability_benign,
        probability_ddos,
        created_at,
        prediction_sequence,
        total_predictions,
        total_ddos,
        total_benign,

        round(
            (
                total_ddos::numeric
                / nullif(total_predictions, 0)
            ) * 100,
            2
        ) as ddos_rate_percent

    from ordered

)

select *
from final