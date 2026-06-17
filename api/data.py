import json, os, traceback
import jwt
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from _helpers import (get_bq, build_campaign_filter, get_token_from_header,
                      json_response, error_response, cors_headers, BQ_TABLE)

BQ_TABLE_SAFE = f"`{BQ_TABLE}`"

def bq_rows(query):
    bq = get_bq()
    return [dict(r) for r in bq.query(query).result()]

def get_kpi(camp_filter, start, end):
    q = f"""
    SELECT
        SUM(COALESCE(IMPRESSIONS, 0))                   AS impressions,
        SUM(COALESCE(CLICKS, 0))                        AS clicks,
        SUM(COALESCE(CLICKS_LINK, 0))                   AS clicks_link,
        SUM(COALESCE(THRUPLAY, 0))                      AS thruplay,
        SUM(COALESCE(VIEWS6,  0))                       AS views6,
        SUM(COALESCE(VIEWS25, 0))                       AS views25,
        SUM(COALESCE(VIEWS50, 0))                       AS views50,
        SUM(COALESCE(VIEWS75, 0))                       AS views75,
        SUM(COALESCE(VIEWS100,0))                       AS views100,
        SUM(COALESCE(total_comments, 0))                AS comments,
        SUM(COALESCE(total_reacoes,  0))                AS reactions,
        SUM(COALESCE(total_salvamentos, 0))             AS saves,
        SUM(COALESCE(total_compartilhamento, 0))        AS shares,
        SAFE_DIVIDE(
            SUM(COALESCE(CLICKS,0)),
            NULLIF(SUM(COALESCE(IMPRESSIONS,0)),0)
        ) * 100  AS ctr,
        SAFE_DIVIDE(
            SUM(COALESCE(THRUPLAY,0)),
            NULLIF(SUM(COALESCE(IMPRESSIONS,0)),0)
        ) * 100  AS vtr
    FROM {BQ_TABLE_SAFE}
    WHERE date BETWEEN '{start}' AND '{end}'
      AND {camp_filter}
    """
    rows = bq_rows(q)
    return rows[0] if rows else {}

def get_timeseries(camp_filter, start, end):
    q = f"""
    SELECT
        CAST(date AS STRING)                            AS date,
        SUM(COALESCE(IMPRESSIONS,0))                   AS impressions,
        SUM(COALESCE(CLICKS,0))                        AS clicks,
        SUM(COALESCE(THRUPLAY,0))                      AS thruplay,
        SUM(COALESCE(VIEWS25,0))                       AS views25,
        SUM(COALESCE(VIEWS50,0))                       AS views50,
        SUM(COALESCE(VIEWS75,0))                       AS views75,
        SUM(COALESCE(VIEWS100,0))                      AS views100,
        SUM(COALESCE(total_comments,0))                AS comments,
        SUM(COALESCE(total_reacoes,0))                 AS reactions,
        SUM(COALESCE(total_salvamentos,0))             AS saves,
        SUM(COALESCE(total_compartilhamento,0))        AS shares,
        SAFE_DIVIDE(
            SUM(COALESCE(CLICKS,0)),
            NULLIF(SUM(COALESCE(IMPRESSIONS,0)),0)
        ) * 100  AS ctr,
        SAFE_DIVIDE(
            SUM(COALESCE(THRUPLAY,0)),
            NULLIF(SUM(COALESCE(IMPRESSIONS,0)),0)
        ) * 100  AS vtr
    FROM {BQ_TABLE_SAFE}
    WHERE date BETWEEN '{start}' AND '{end}'
      AND {camp_filter}
    GROUP BY date
    ORDER BY date ASC
    """
    return bq_rows(q)

def get_by_campaign(camp_filter, start, end):
    q = f"""
    SELECT
        platform,
        CAMPAIGN_NAME,
        SUM(COALESCE(IMPRESSIONS,0))   AS impressions,
        SUM(COALESCE(CLICKS,0))        AS clicks,
        SUM(COALESCE(CLICKS_LINK,0))   AS clicks_link,
        SUM(COALESCE(THRUPLAY,0))      AS thruplay,
        SUM(COALESCE(VIEWS25,0))       AS views25,
        SUM(COALESCE(VIEWS50,0))       AS views50,
        SUM(COALESCE(VIEWS75,0))       AS views75,
        SUM(COALESCE(VIEWS100,0))      AS views100,
        SAFE_DIVIDE(
            SUM(COALESCE(CLICKS,0)),
            NULLIF(SUM(COALESCE(IMPRESSIONS,0)),0)
        ) * 100  AS ctr,
        SAFE_DIVIDE(
            SUM(COALESCE(THRUPLAY,0)),
            NULLIF(SUM(COALESCE(IMPRESSIONS,0)),0)
        ) * 100  AS vtr
    FROM {BQ_TABLE_SAFE}
    WHERE date BETWEEN '{start}' AND '{end}'
      AND {camp_filter}
    GROUP BY platform, CAMPAIGN_NAME
    ORDER BY impressions DESC
    """
    return bq_rows(q)

def get_by_influencer(camp_filter, start, end):
    q = f"""
    SELECT
        CASE
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'lucasguedez')                                          THEN 'lucasguedez'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'sofiasantino')                                         THEN 'sofiasantino'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'eunalumoura')                                          THEN 'eunalumoura'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'nellyhongval')                                         THEN 'nellyhongval'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'trizhermano')                                          THEN 'trizhermano'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'thamiresrangeel')                                     THEN 'thamiresrangeel'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'belezacomari')                                         THEN 'belezacomari'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'albaropaula')                                          THEN 'albaropaula'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'ciclopin')                                             THEN 'ciclopin'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'danmendesoficial')                                     THEN 'danmendesoficial'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'herdeiradabeleza')                                     THEN 'herdeiradabeleza'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'abcdapele')                                            THEN 'abcdapele'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'amandaapoxa')                                          THEN 'amandaapoxa'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'brunanaomisaito')                                      THEN 'brunanaomisaito'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'julianaluziee')                                        THEN 'julianaluziee'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'drursinhocarinhoso')                                   THEN 'drursinhocarinhoso'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'natymeirelesoficial')                                  THEN 'natymeirelesoficial'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'jardeledebran')                                        THEN 'jardeledebran'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'carolinnegas')                                         THEN 'carolinnegas'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'rufislore')                                            THEN 'rufislore'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'keirariff')                                            THEN 'keirariff'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'bomtalvao')                                            THEN 'bomtalvao'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'vitoria jansen|vitória jansen')                        THEN 'Vitória Jansen'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'julia stofel')                                         THEN 'Julia Stofel'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'gih gallotti')                                         THEN 'Gih Gallotti'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'vivie nkenda')                                         THEN 'Vivie Nkenda'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'beatriz macedo')                                       THEN 'Beatriz Macedo'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'vitor maciel')                                         THEN 'Vitor Maciel'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'weslley andrade')                                      THEN 'Weslley Andrade'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'mayara rodrigues')                                     THEN 'Mayara Rodrigues'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'sthefany vitoria|sthefany vitória|sthefany thais')    THEN 'Sthefany Vitória'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'celma barbosa')                                        THEN 'Celma Barbosa'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'katiane lima')                                         THEN 'Katiane Lima'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'gabe zanchi')                                          THEN 'Gabe Zanchi'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'antonella vanoni')                                     THEN 'Antonella Vanoni'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'gab lobo')                                             THEN 'Gab Lobo'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'giovanna fonseca')                                     THEN 'Giovanna Fonseca'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'dayellen')                                             THEN 'Dayellen'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'alan vivian')                                          THEN 'Alan Vivian'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'silvonei')                                             THEN 'Silvonei'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'bruno evangelista')                                    THEN 'Bruno Evangelista'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'rauany barcellos')                                     THEN 'Rauany Barcellos'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'karoline lima')                                        THEN 'Karoline Lima'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'dani cacella')                                         THEN 'Dani Cacella'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'dodo mendonça|dodo mendonca')                          THEN 'Dodo Mendonça'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'bil araujo')                                           THEN 'Bil Araujo'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'camila loures')                                        THEN 'Camila Loures'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'pati liberato')                                        THEN 'Pati Liberato'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'gabriel dantas')                                       THEN 'Gabriel Dantas'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'cath')                                                 THEN 'Cath'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'rebimboca')                                            THEN 'Rebimboca'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'hiane luiza')                                          THEN 'Hiane Luiza'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'drica divina')                                         THEN 'Drica Divina'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'lu borgatto')                                          THEN 'Lu Borgatto'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'carol priante')                                        THEN 'Carol Priante'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'gabriel braga')                                        THEN 'Gabriel Braga'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'wesley soares')                                        THEN 'Wesley Soares'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'canal bra')                                            THEN 'Canal Bra'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'hugo souza')                                           THEN 'Hugo Souza'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'bruna naomi')                                          THEN 'Bruna Naomi'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'lua lino')                                             THEN 'Lua Lino'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'nath carvalho')                                        THEN 'Nath Carvalho'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'giovana')                                              THEN 'Giovana'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'cesar')                                                THEN 'Cesar'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'jose luis')                                            THEN 'Jose Luis'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'norma')                                                THEN 'Norma'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'weena')                                                THEN 'Weena'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'coala')                                                THEN 'Coala'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'marina')                                               THEN 'Marina'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'angel')                                                THEN 'Angel'
            WHEN REGEXP_CONTAINS(LOWER(AD_NAME), 'eve')                                                  THEN 'Eve'
            ELSE NULL
        END AS influenciador,
        platform,
        CAMPAIGN_NAME,
        SUM(COALESCE(IMPRESSIONS,   0))                            AS impressions,
        SUM(COALESCE(CLICKS_LINK,   0))                            AS clicks_link,
        SUM(COALESCE(CLICKS,        0))                            AS clicks,
        SUM(COALESCE(THRUPLAY,      0))                            AS thruplay,
        SUM(COALESCE(VIEWS25,       0))                            AS views25,
        SUM(COALESCE(VIEWS50,       0))                            AS views50,
        SUM(COALESCE(VIEWS75,       0))                            AS views75,
        SUM(COALESCE(VIEWS100,      0))                            AS views100,
        SUM(COALESCE(total_comments,       0))                     AS comments,
        SUM(COALESCE(total_reacoes,        0))                     AS reactions,
        SUM(COALESCE(total_salvamentos,    0))                     AS saves,
        SUM(COALESCE(total_compartilhamento, 0))                   AS shares,
        SAFE_DIVIDE(
            SUM(COALESCE(CLICKS_LINK, 0)),
            NULLIF(SUM(COALESCE(IMPRESSIONS, 0)), 0)
        ) * 100  AS ctr_link,
        SAFE_DIVIDE(
            SUM(COALESCE(CLICKS, 0)),
            NULLIF(SUM(COALESCE(IMPRESSIONS, 0)), 0)
        ) * 100  AS ctr_click,
        SAFE_DIVIDE(
            SUM(COALESCE(THRUPLAY, 0)),
            NULLIF(SUM(COALESCE(IMPRESSIONS, 0)), 0)
        ) * 100  AS vtr
    FROM {BQ_TABLE_SAFE}
    WHERE date BETWEEN '{start}' AND '{end}'
      AND {camp_filter}
    GROUP BY influenciador, platform, CAMPAIGN_NAME
    HAVING influenciador IS NOT NULL
    ORDER BY impressions DESC
    """
    return bq_rows(q)


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        for k, v in cors_headers().items(): self.send_header(k, v)
        self.end_headers()

    def _send(self, resp):
        self.send_response(resp["statusCode"])
        for k, v in resp["headers"].items(): self.send_header(k, v)
        self.end_headers()
        self.wfile.write(resp["body"].encode())

    def do_GET(self):
        try:
            user = get_token_from_header(self.headers)

            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            start  = params.get("start_date", [""])[0]
            end    = params.get("end_date",   [""])[0]
            type_  = params.get("type",       ["kpi"])[0]

            if not start or not end:
                return self._send(error_response("Parâmetros start_date e end_date obrigatórios."))

            camp_filter = build_campaign_filter(user)

            if type_ == "kpi":
                result = get_kpi(camp_filter, start, end)
            elif type_ == "timeseries":
                result = {"rows": get_timeseries(camp_filter, start, end)}
            elif type_ == "by_campaign":
                result = {"rows": get_by_campaign(camp_filter, start, end)}
            elif type_ == "by_influencer":
                result = {"rows": get_by_influencer(camp_filter, start, end)}
            else:
                return self._send(error_response("Tipo inválido."))

            self._send(json_response(result))

        except (PermissionError, jwt.ExpiredSignatureError) as e:
            self._send(error_response(str(e), 401))
        except Exception as e:
            # Retorna o traceback completo como resposta para debug
            tb = traceback.format_exc()
            self._send(error_response(f"ERRO: {str(e)} | TRACEBACK: {tb}", 500))
