select
    l.id,
    l.email_normalized,
    l.status,
    qr.deterministic_score,
    qr.qualification_status,
    qr.final_status,
    qr.score_breakdown,
    qr.ai_confidence,
    qr.ai_review_reasons,
    qr.ai_result
from public.leads l
join public.qualification_results qr
    on qr.lead_id = l.id
where l.email_normalized like
    'delivered+leadflow-cold-no-consent-%@resend.dev'
order by l.created_at desc
limit 1;