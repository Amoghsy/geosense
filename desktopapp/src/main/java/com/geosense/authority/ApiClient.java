package com.geosense.authority;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Java 17 HttpClient wrapper connecting the JavaFX Authority Command Center
 * to the GeoSense FastAPI Backend (Phases 1-9).
 */
public class ApiClient {
    private String baseUrl;
    private String jwtToken;
    private final HttpClient http;

    public ApiClient(String baseUrl) {
        this.baseUrl = baseUrl.replaceAll("/+$", "");
        this.http = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .build();
    }

    public void setBaseUrl(String baseUrl) {
        this.baseUrl = baseUrl.replaceAll("/+$", "");
    }

    public String getBaseUrl() {
        return baseUrl;
    }

    public String getToken() {
        return jwtToken;
    }

    public String request(String method, String path, String jsonBody) throws Exception {
        HttpRequest.Builder builder = HttpRequest.newBuilder()
                .uri(URI.create(baseUrl + path))
                .timeout(Duration.ofSeconds(25))
                .header("Content-Type", "application/json");

        if (jwtToken != null && !jwtToken.isEmpty()) {
            builder.header("Authorization", "Bearer " + jwtToken);
        }

        if ("POST".equalsIgnoreCase(method) || "PATCH".equalsIgnoreCase(method)) {
            builder.method(method.toUpperCase(), HttpRequest.BodyPublishers.ofString(jsonBody == null ? "{}" : jsonBody));
        } else {
            builder.GET();
        }

        HttpResponse<String> resp = http.send(builder.build(), HttpResponse.BodyHandlers.ofString());
        if (resp.statusCode() >= 400) {
            throw new RuntimeException("HTTP " + resp.statusCode() + ": " + resp.body());
        }
        return resp.body();
    }

    public String login(String email, String password) throws Exception {
        String body = String.format("{\"email\":\"%s\",\"password\":\"%s\"}", escapeJson(email), escapeJson(password));
        String resp = request("POST", "/auth/login", body);
        this.jwtToken = extractJsonString(resp, "access_token");
        return resp;
    }

    public String registerAuthority(String email, String password, String fullName, String provisionSecret) throws Exception {
        String body = String.format(
                "{\"email\":\"%s\",\"password\":\"%s\",\"full_name\":\"%s\",\"role\":\"AUTHORITY\",\"provision_secret\":\"%s\"}",
                escapeJson(email), escapeJson(password), escapeJson(fullName), escapeJson(provisionSecret)
        );
        String resp = request("POST", "/auth/register", body);
        this.jwtToken = extractJsonString(resp, "access_token");
        return resp;
    }

    public String getAuthorityDashboard() throws Exception {
        return request("GET", "/authority/dashboard", null);
    }

    public String getAuthorityAnalytics() throws Exception {
        return request("GET", "/authority/analytics", null);
    }

    public String getAuthorityIncidents() throws Exception {
        return request("GET", "/authority/incidents", null);
    }

    public String verifyIncident(String incidentId, String status, String notes) throws Exception {
        String body = String.format("{\"status\":\"%s\",\"verification_notes\":\"%s\"}", escapeJson(status), escapeJson(notes));
        return request("POST", "/incidents/" + incidentId + "/verify", body);
    }

    public String assignIncident(String incidentId, String officerId, String notes) throws Exception {
        String body = String.format("{\"officer_id\":\"%s\",\"notes\":\"%s\"}", escapeJson(officerId), escapeJson(notes));
        return request("POST", "/authority/incidents/" + incidentId + "/assign", body);
    }

    public String getInspections() throws Exception {
        return request("GET", "/inspections", null);
    }

    public String getResources() throws Exception {
        return request("GET", "/resources?role=authority", null);
    }

    public String createResource(String name, String type, String state, double lat, double lon) throws Exception {
        String body = String.format(
                "{\"resource_name\":\"%s\",\"resource_type\":\"%s\",\"state\":\"%s\",\"latitude\":%f,\"longitude\":%f,\"is_public_contact\":true}",
                escapeJson(name), escapeJson(type), escapeJson(state), lat, lon
        );
        return request("POST", "/resources?role=authority", body);
    }

    public String verifyResource(String resourceId, String verificationStatus) throws Exception {
        String op = "VERIFIED".equals(verificationStatus) ? "OPERATIONAL" : "CLOSED";
        String avail = "VERIFIED".equals(verificationStatus) ? "AVAILABLE" : "UNAVAILABLE";
        String body = String.format(
                "{\"verification_status\":\"%s\",\"operational_status\":\"%s\",\"availability_status\":\"%s\"}",
                verificationStatus, op, avail
        );
        return request("POST", "/resources/" + resourceId + "/verify?role=authority", body);
    }

    public String analyzeRisk(double lat, double lon, String locName, double elev, double slope) throws Exception {
        String body = String.format(
                "{\"latitude\":%f,\"longitude\":%f,\"location_name\":\"%s\",\"elevation_m\":%f,\"slope_deg\":%f}",
                lat, lon, escapeJson(locName), elev, slope
        );
        return request("POST", "/risk/analyze", body);
    }

    public String getRiskTrends(String locationId) throws Exception {
        return request("GET", "/risk/" + locationId + "/trends", null);
    }

    public String getContributingFactors(String assessmentId) throws Exception {
        return request("GET", "/risk/" + assessmentId + "/contributing-factors", null);
    }

    public String getGisHotspots() throws Exception {
        return request("GET", "/gis/hotspots", null);
    }

    public String getGisRiskFeatures() throws Exception {
        return request("GET", "/gis/layers/phase3_dynamic_risk/features?limit=50", null);
    }

    public String generateSituationReport(String regionId) throws Exception {
        String regPart = (regionId == null || regionId.isBlank()) ? "null" : "\"" + escapeJson(regionId) + "\"";
        String body = String.format("{\"region_id\":%s,\"role\":\"authority\"}", regPart);
        return request("POST", "/authority/situation-reports", body);
    }

    public String getAuditLogs() throws Exception {
        return request("GET", "/authority/audit-logs?limit=25", null);
    }

    public String askAgent(String message) throws Exception {
        String body = String.format("{\"message\":\"%s\",\"role\":\"authority\"}", escapeJson(message));
        return request("POST", "/agent/chat", body);
    }

    public String getAlerts() throws Exception {
        return request("GET", "/alerts", null);
    }

    public String generateAlertsForAssessment(String assessmentId) throws Exception {
        String body = String.format("{\"assessment_id\":\"%s\"}", escapeJson(assessmentId));
        return request("POST", "/alerts/generate", body);
    }

    public String approveAlert(String alertId, String notes) throws Exception {
        String body = String.format("{\"admin_notes\":\"%s\",\"expiry_hours\":24}", escapeJson(notes));
        return request("POST", "/alerts/" + alertId + "/approve", body);
    }

    public String rejectAlert(String alertId, String notes) throws Exception {
        String body = String.format("{\"admin_notes\":\"%s\"}", escapeJson(notes));
        return request("POST", "/alerts/" + alertId + "/reject", body);
    }

    public String publishAlert(String alertId, String notes) throws Exception {
        String body = String.format("{\"admin_notes\":\"%s\"}", escapeJson(notes));
        return request("POST", "/alerts/" + alertId + "/publish", body);
    }

    public String getAlertDeliveries(String alertId) throws Exception {
        return request("GET", "/alerts/" + alertId + "/deliveries", null);
    }

    public String getChannelStatus() throws Exception {
        return request("GET", "/alerts/status", null);
    }

    public static String extractJsonString(String json, String key) {
        Matcher m = Pattern.compile("\"" + Pattern.quote(key) + "\"\\s*:\\s*\"([^\"]*)\"").matcher(json);
        return m.find() ? m.group(1) : "";
    }

    public static String extractJsonNumber(String json, String key) {
        Matcher m = Pattern.compile("\"" + Pattern.quote(key) + "\"\\s*:\\s*(-?\\d+(?:\\.\\d+)?)").matcher(json);
        return m.find() ? m.group(1) : "0";
    }

    public static List<String> splitJsonObjectsInArray(String json, String arrayKey) {
        List<String> items = new ArrayList<>();
        int keyIdx = json.indexOf("\"" + arrayKey + "\"");
        if (keyIdx < 0) return items;
        int arrStart = json.indexOf('[', keyIdx);
        if (arrStart < 0) return items;
        int depth = 0;
        int objStart = -1;
        for (int i = arrStart + 1; i < json.length(); i++) {
            char c = json.charAt(i);
            if (c == '{') {
                if (depth == 0) objStart = i;
                depth++;
            } else if (c == '}') {
                depth--;
                if (depth == 0 && objStart >= 0) {
                    items.add(json.substring(objStart, i + 1));
                    objStart = -1;
                }
            } else if (c == ']' && depth == 0) {
                break;
            }
        }
        return items;
    }

    private static String escapeJson(String s) {
        return s == null ? "" : s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n");
    }
}
