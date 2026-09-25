# VR Liaoyucang backend

The backend is mounted at `/vr/` and `/api/vr/`. It uses the normal Django
session cookie for anonymous ownership. A browser first calls
`GET /api/vr/config/`; the response includes `csrfToken` and also sets the
Django CSRF cookie. Send that token in `X-CSRFToken` on every browser POST.

The public flow is:

1. `POST /api/vr/sessions/` with `{"consent":true,"companion":"xiaoxuan"}`
   or `xiaoxing`.
2. `POST /api/vr/sessions/<id>/assessments/` with a `before` or `after` stage
   and exactly 20 integer `responses` in the range 1 through 4. The server
   computes STAI-S using reverse indexes `0,1,4,7,9,10,14,15,18,19`.
3. `POST /api/vr/sessions/<id>/recommendation/` with `goal`, `instrument`,
   `tone`, `soundscape`, and optional `scene`.
4. `POST /api/vr/sessions/<id>/experience/` for `start`, `complete`, or
   `abandon`. The server checks the saved plan, duration, and ownership; it
   never trusts a client video URL.
5. `GET /api/vr/sessions/<id>/report/`, then POST `/analysis/` after both
   assessments exist.

Questionnaire assessments contain null basic, EEG, emotion, and device values.
No baseline device data or risk classification is synthesized from the
questionnaire score. The current device setting is intentionally disabled.

The optional device ingestion endpoint is server-to-server only:

```http
POST /api/vr/device-assessments/
Authorization: Bearer <VR_DEVICE_API_KEY>
Content-Type: application/json
```

```json
{
  "sessionId": "00000000-0000-0000-0000-000000000000",
  "stage": "before",
  "basic": {"heartRate": 72, "respiration": 15.2},
  "eeg": {"alpha": 24.1},
  "emotion": {"neutral": 0.8},
  "device": {"eyeX": 0.46, "eyeY": 0.34},
  "series": {"heartRate": [72, 72.2, 71.9]}
}
```

The endpoint accepts only the documented normalized scalar groups, finite
numbers, and at most 1,000 values per series. It updates the exact session and
stage named by the request; there is no “latest user” lookup. If
`VR_DEVICE_API_KEY` is absent it returns `503` and the public config keeps
`deviceConfigured: false`.

Media is read from `VR_MEDIA_CATALOG_PATH`, defaulting to
`static/vr/assets/data/recommendation-catalog-v2.json`. Entries without a
playable URL are ignored. The three verified repository videos are used as a
small fallback catalog: `2_27.mp4`, `2_25.mp4`, and `2_10.mp4`. Set
`VR_MEDIA_BASE_URL` to the CDN directory that contains the catalog's relative
asset paths, for example `https://cdn.example.com/vr`; generated URLs then use
`https://cdn.example.com/vr/assets/...`.

AI analysis is disabled until a key is configured. Set `VR_AI_API_KEY`,
`VR_AI_MODEL`, and optionally `VR_AI_BASE_URL`. `VR_AI_BASE_URL` can be the
full endpoint (`.../v1/text/chatcompletion_v2`), a `/v1` base, or a host base;
the backend appends the MiniMax-compatible path as needed. If
`VR_AI_API_KEY` is absent, `MINIMAX_API_KEY` is used with the default endpoint
`https://api.minimaxi.com/v1/text/chatcompletion_v2` and model
`MiniMax-M2.5`. Calls are capped by a 45 second timeout and 300 output tokens.
AI failures are stored as `failed` without returning upstream details; missing
configuration is stored as `unavailable`. Successful results are cached for
the current assessment revision.
