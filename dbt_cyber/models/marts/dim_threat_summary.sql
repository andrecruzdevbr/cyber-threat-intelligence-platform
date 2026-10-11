with summary as (

    select
        class,
        count(*) as total_predictions,
        avg(probability_benign) as avg_probability_benign,
        avg(probability_ddos) as avg_probability_ddos,
        min(created_at) as first_prediction_at,
        max(created_at) as last_prediction_at

    from {{ ref('stg_predictions') }}

    group by class

)

select *
from summary