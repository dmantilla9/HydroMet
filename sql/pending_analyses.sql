WITH pending_analyses AS (
    SELECT
        cr.id,
        cr.commune,
        ig.date_prelevement,
        co.conclusions_sanitaires,
        co.conformite_bacteriologique,
        co.conformite_physico_chimique,
        co.respect_references_qualite
    FROM fait_anl_criteres_recherche cr
    INNER JOIN fait_anl_informations_generales ig
        ON cr.id = ig.id
    LEFT JOIN fait_anl_conformite co
        ON cr.id = co.id
    WHERE cr.commune = %s
      AND NOT EXISTS (
          SELECT 1
          FROM hydromet_notification_history nh
          WHERE nh.analysis_id = cr.id
            AND nh.notification_channel = %s
            AND nh.status IN ('sent', 'baseline')
      )
)
SELECT
    pa.id,
    pa.date_prelevement,
    jsonb_build_object(
        'id', pa.id,
        'commune', pa.commune,
        'date_prelevement', pa.date_prelevement,
        'conformite', jsonb_build_object(
            'conclusions', pa.conclusions_sanitaires,
            'bacteriologique', pa.conformite_bacteriologique,
            'physico_chimique', pa.conformite_physico_chimique,
            'references_qualite', pa.respect_references_qualite
        ),
        'resultats', COALESCE(
            (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'parametre', ra.parametre,
                        'valeur', ra.valeur,
                        'limite_qualite', ra.limite_qualite,
                        'reference_qualite', ra.reference_qualite
                    )
                    ORDER BY ra.parametre
                )
                FROM fait_anl_resultats_analyses ra
                WHERE ra.id = pa.id
            ),
            '[]'::jsonb
        )
    ) AS notification_payload
FROM pending_analyses pa
ORDER BY pa.date_prelevement DESC NULLS LAST, pa.id DESC;
