# Agent Run Summary (client_impact)

Run ID: `20260304T205208Z`

| Job | Status | Summary |
|---|---|---|
| ga4_audit | attention | GA4 audited 1 properties, 1 with findings |
- ga4_audit: 123456789: Failed to read data streams: HTTP 403: {"error": {"code": 403, "message": "Request had insufficient authentication scopes.", "status": "PERMISSION_DENIED", "details": [{"@type": "type.googleapis.com/google.rpc.ErrorInfo", "reason": "ACCESS_TOKEN_SCOPE_INSUFFICIENT", "domain": "googleapis.com", "metadata": {"method": "google.analytics.admin.v1beta.AnalyticsAdminService.ListDataStreams", "service": "analyticsadmin.googleapis.com"}}]}}
- ga4_audit: 123456789: Failed to run GA4 report: HTTP 403: {"error": {"code": 403, "message": "Request had insufficient authentication scopes.", "status": "PERMISSION_DENIED", "details": [{"@type": "type.googleapis.com/google.rpc.ErrorInfo", "reason": "ACCESS_TOKEN_SCOPE_INSUFFICIENT", "domain": "googleapis.com", "metadata": {"service": "analyticsdata.googleapis.com", "method": "google.analytics.data.v1beta.BetaAnalyticsData.RunReport"}}]}}
- artifact: reports/agent_runs/20260304T205208Z_client_impact/ga4_audit.json
| gtm_audit | attention | GTM audited 1 containers, 1 findings |
- gtm_audit: accounts/1234567/containers/7654321: GTM API error: HTTP 403: {"error": {"code": 403, "message": "Request had insufficient authentication scopes.", "errors": [{"message": "Insufficient Permission", "domain": "global", "reason": "insufficientPermissions"}], "status": "PERMISSION_DENIED", "details": [{"@type": "type.googleapis.com/google.rpc.ErrorInfo", "reason": "ACCESS_TOKEN_SCOPE_INSUFFICIENT", "domain": "googleapis.com", "metadata": {"method": "container_tag.apiary_v2.TagManagerServiceV2.ListWorkspaces", "service": "tagmanager.googleapis.com"}}]}}
- artifact: reports/agent_runs/20260304T205208Z_client_impact/gtm_audit.json
| kpi_daily_digest | attention | Generated KPI digest for 0 properties |
- kpi_daily_digest: 123456789: KPI pull failed: HTTP 403: {"error": {"code": 403, "message": "Request had insufficient authentication scopes.", "status": "PERMISSION_DENIED", "details": [{"@type": "type.googleapis.com/google.rpc.ErrorInfo", "reason": "ACCESS_TOKEN_SCOPE_INSUFFICIENT", "domain": "googleapis.com", "metadata": {"service": "analyticsdata.googleapis.com", "method": "google.analytics.data.v1beta.BetaAnalyticsData.RunReport"}}]}}
- artifact: reports/agent_runs/20260304T205208Z_client_impact/kpi_daily_digest.json
- artifact: reports/agent_runs/20260304T205208Z_client_impact/kpi_daily_digest.md
