package com.geosense.authority;

import javafx.application.Application;
import javafx.application.Platform;
import javafx.beans.property.SimpleStringProperty;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Scene;
import javafx.scene.control.*;
import javafx.scene.layout.*;
import javafx.stage.Stage;

import java.util.List;

/**
 * GeoSense Disaster Management Authority Desktop Application (JavaFX).
 * Connects directly to the GeoSense FastAPI Backend (Phases 1-8).
 */
public class GeoSenseAuthorityApp extends Application {

    private final ApiClient api = new ApiClient("http://localhost:8000");

    private Label authStatusLabel;
    private Label kpiRiskLocs;
    private Label kpiHighCrit;
    private Label kpiPendingInc;
    private Label kpiVerifiedRes;
    private Label kpiInspections;

    private final ObservableList<IncidentRow> incidentRows = FXCollections.observableArrayList();
    private final ObservableList<ResourceRow> resourceRows = FXCollections.observableArrayList();
    private final ObservableList<AlertRow> alertRows = FXCollections.observableArrayList();
    private TextArea reportArea;
    private TextArea auditArea;
    private TextArea agentChatArea;
    private TextArea alertDeliveriesArea;

    @Override
    public void start(Stage stage) {
        stage.setTitle("GeoSense — Disaster Management Authority Desktop (JavaFX)");

        BorderPane root = new BorderPane();
        root.setStyle("-fx-background-color: #0f172a; -fx-font-family: 'Segoe UI', sans-serif;");

        // Top Auth & Connection Bar
        HBox topBar = buildTopBar();
        root.setTop(topBar);

        // Center TabPane
        TabPane tabs = new TabPane();
        tabs.setTabClosingPolicy(TabPane.TabClosingPolicy.UNAVAILABLE);
        tabs.getTabs().addAll(
                buildOverviewTab(),
                buildIncidentsTab(),
                buildResourcesTab(),
                buildAlertsTab(),
                buildReportsAndAuditTab(),
                buildAgentTab()
        );
        root.setCenter(tabs);

        Scene scene = new Scene(root, 1220, 760);
        stage.setScene(scene);
        stage.show();
    }

    private HBox buildTopBar() {
        TextField backendField = new TextField("http://localhost:8000");
        backendField.setPrefWidth(180);
        TextField emailField = new TextField("authority@geosense.in");
        emailField.setPrefWidth(180);
        PasswordField passField = new PasswordField();
        passField.setText("Authority@123");
        passField.setPrefWidth(130);

        Button loginBtn = new Button("Login");
        loginBtn.setStyle("-fx-background-color: #38bdf8; -fx-text-fill: #0f172a; -fx-font-weight: bold;");
        Button regBtn = new Button("Provision & Login");
        regBtn.setStyle("-fx-background-color: #f59e0b; -fx-text-fill: #0f172a; -fx-font-weight: bold;");
        Button refreshBtn = new Button("Refresh Data");

        authStatusLabel = new Label("Not authenticated");
        authStatusLabel.setStyle("-fx-text-fill: #94a3b8; -fx-font-size: 12px;");

        loginBtn.setOnAction(e -> runAsync(() -> {
            api.setBaseUrl(backendField.getText().trim());
            api.login(emailField.getText().trim(), passField.getText());
            Platform.runLater(() -> authStatusLabel.setText("Authenticated as Authority"));
            refreshAllData();
        }));

        regBtn.setOnAction(e -> runAsync(() -> {
            api.setBaseUrl(backendField.getText().trim());
            api.registerAuthority(emailField.getText().trim(), passField.getText(), "NDMA Regional Authority", "geosense-admin-provision");
            Platform.runLater(() -> authStatusLabel.setText("Provisioned & Authenticated"));
            refreshAllData();
        }));

        refreshBtn.setOnAction(e -> runAsync(this::refreshAllData));

        HBox bar = new HBox(10,
                new Label("Backend:") {{ setStyle("-fx-text-fill: #cbd5e1;"); }}, backendField,
                new Label("Email:") {{ setStyle("-fx-text-fill: #cbd5e1;"); }}, emailField,
                passField, loginBtn, regBtn, refreshBtn, authStatusLabel
        );
        bar.setAlignment(Pos.CENTER_LEFT);
        bar.setPadding(new Insets(12));
        bar.setStyle("-fx-background-color: #1e293b; -fx-border-color: #334155; -fx-border-width: 0 0 1 0;");
        return bar;
    }

    private Tab buildOverviewTab() {
        kpiRiskLocs = makeKpiLabel("0");
        kpiHighCrit = makeKpiLabel("0");
        kpiPendingInc = makeKpiLabel("0");
        kpiVerifiedRes = makeKpiLabel("0");
        kpiInspections = makeKpiLabel("0");

        HBox kpiRow = new HBox(14,
                makeKpiCard("Risk Locations", kpiRiskLocs),
                makeKpiCard("High / Critical", kpiHighCrit),
                makeKpiCard("Pending Incidents", kpiPendingInc),
                makeKpiCard("Verified Resources", kpiVerifiedRes),
                makeKpiCard("Field Inspections", kpiInspections)
        );
        kpiRow.setPadding(new Insets(16));

        Label note = new Label(
                "GeoSense Authority Command Console (JavaFX)\n" +
                "• Connected to FastAPI Phases 1-8 Backend\n" +
                "• Risk indices are provisional heuristic scores (0-100), not calibrated probabilities.\n" +
                "• Citizen incident reports require officer/authority verification before confirmation."
        );
        note.setStyle("-fx-text-fill: #cbd5e1; -fx-font-size: 13px; -fx-padding: 16; -fx-background-color: #1e293b; -fx-background-radius: 8;");

        VBox box = new VBox(16, kpiRow, note);
        box.setPadding(new Insets(16));
        return new Tab("Overview", box);
    }

    private Tab buildIncidentsTab() {
        TableView<IncidentRow> table = new TableView<>(incidentRows);
        TableColumn<IncidentRow, String> cId = new TableColumn<>("ID");
        cId.setCellValueFactory(d -> d.getValue().id);
        TableColumn<IncidentRow, String> cCat = new TableColumn<>("Category");
        cCat.setCellValueFactory(d -> d.getValue().category);
        TableColumn<IncidentRow, String> cState = new TableColumn<>("State");
        cState.setCellValueFactory(d -> d.getValue().state);
        TableColumn<IncidentRow, String> cStatus = new TableColumn<>("Status");
        cStatus.setCellValueFactory(d -> d.getValue().status);
        TableColumn<IncidentRow, String> cDesc = new TableColumn<>("Description");
        cDesc.setCellValueFactory(d -> d.getValue().description);
        cDesc.setPrefWidth(380);
        table.getColumns().addAll(cId, cCat, cState, cStatus, cDesc);

        Button verifyBtn = new Button("Verify Selected");
        verifyBtn.setStyle("-fx-background-color: #10b981; -fx-text-fill: #0f172a; -fx-font-weight: bold;");
        Button rejectBtn = new Button("Reject Selected");
        rejectBtn.setStyle("-fx-background-color: #ef4444; -fx-text-fill: white; -fx-font-weight: bold;");

        verifyBtn.setOnAction(e -> {
            IncidentRow sel = table.getSelectionModel().getSelectedItem();
            if (sel != null) runAsync(() -> {
                api.verifyIncident(sel.id.get(), "VERIFIED", "Verified via JavaFX Authority Desktop");
                refreshAllData();
            });
        });
        rejectBtn.setOnAction(e -> {
            IncidentRow sel = table.getSelectionModel().getSelectedItem();
            if (sel != null) runAsync(() -> {
                api.verifyIncident(sel.id.get(), "REJECTED", "Rejected via JavaFX Authority Desktop");
                refreshAllData();
            });
        });

        HBox actions = new HBox(10, verifyBtn, rejectBtn);
        VBox box = new VBox(12, actions, table);
        box.setPadding(new Insets(16));
        return new Tab("Incident Management", box);
    }

    private Tab buildResourcesTab() {
        TableView<ResourceRow> table = new TableView<>(resourceRows);
        TableColumn<ResourceRow, String> cId = new TableColumn<>("ID");
        cId.setCellValueFactory(d -> d.getValue().id);
        TableColumn<ResourceRow, String> cName = new TableColumn<>("Facility Name");
        cName.setCellValueFactory(d -> d.getValue().name);
        cName.setPrefWidth(240);
        TableColumn<ResourceRow, String> cType = new TableColumn<>("Category");
        cType.setCellValueFactory(d -> d.getValue().type);
        TableColumn<ResourceRow, String> cVer = new TableColumn<>("Verification");
        cVer.setCellValueFactory(d -> d.getValue().verification);
        TableColumn<ResourceRow, String> cOp = new TableColumn<>("Operational");
        cOp.setCellValueFactory(d -> d.getValue().operational);
        TableColumn<ResourceRow, String> cAvail = new TableColumn<>("Availability");
        cAvail.setCellValueFactory(d -> d.getValue().availability);
        table.getColumns().addAll(cId, cName, cType, cVer, cOp, cAvail);

        Button verifyBtn = new Button("Verify Resource");
        verifyBtn.setStyle("-fx-background-color: #10b981; -fx-text-fill: #0f172a; -fx-font-weight: bold;");
        Button rejectBtn = new Button("Reject Resource");
        rejectBtn.setStyle("-fx-background-color: #ef4444; -fx-text-fill: white; -fx-font-weight: bold;");

        verifyBtn.setOnAction(e -> {
            ResourceRow sel = table.getSelectionModel().getSelectedItem();
            if (sel != null) runAsync(() -> {
                api.verifyResource(sel.id.get(), "VERIFIED");
                refreshAllData();
            });
        });
        rejectBtn.setOnAction(e -> {
            ResourceRow sel = table.getSelectionModel().getSelectedItem();
            if (sel != null) runAsync(() -> {
                api.verifyResource(sel.id.get(), "REJECTED");
                refreshAllData();
            });
        });

        HBox actions = new HBox(10, verifyBtn, rejectBtn);
        VBox box = new VBox(12, actions, table);
        box.setPadding(new Insets(16));
        return new Tab("Emergency Resources", box);
    }

    private Tab buildAlertsTab() {
        TableView<AlertRow> table = new TableView<>(alertRows);
        TableColumn<AlertRow, String> cId = new TableColumn<>("Alert ID");
        cId.setCellValueFactory(d -> d.getValue().id);
        TableColumn<AlertRow, String> cSev = new TableColumn<>("Severity");
        cSev.setCellValueFactory(d -> d.getValue().severity);
        TableColumn<AlertRow, String> cTitle = new TableColumn<>("Title");
        cTitle.setCellValueFactory(d -> d.getValue().title);
        cTitle.setPrefWidth(260);
        TableColumn<AlertRow, String> cState = new TableColumn<>("State");
        cState.setCellValueFactory(d -> d.getValue().state);
        TableColumn<AlertRow, String> cStatus = new TableColumn<>("Approval");
        cStatus.setCellValueFactory(d -> d.getValue().status);
        table.getColumns().addAll(cId, cSev, cTitle, cState, cStatus);

        Button appBtn = new Button("Approve");
        appBtn.setStyle("-fx-background-color: #38bdf8; -fx-text-fill: #0f172a; -fx-font-weight: bold;");
        Button pubBtn = new Button("Publish (Email + FCM)");
        pubBtn.setStyle("-fx-background-color: #10b981; -fx-text-fill: #0f172a; -fx-font-weight: bold;");
        Button rejBtn = new Button("Reject");
        rejBtn.setStyle("-fx-background-color: #ef4444; -fx-text-fill: white; -fx-font-weight: bold;");
        Button delBtn = new Button("View Deliveries");

        alertDeliveriesArea = new TextArea("Select an alert and click 'View Deliveries' to inspect Email & FCM logs.");
        alertDeliveriesArea.setEditable(false);
        alertDeliveriesArea.setPrefHeight(160);

        appBtn.setOnAction(e -> {
            AlertRow sel = table.getSelectionModel().getSelectedItem();
            if (sel != null) runAsync(() -> { api.approveAlert(sel.id.get(), "Approved in JavaFX"); refreshAllData(); });
        });
        pubBtn.setOnAction(e -> {
            AlertRow sel = table.getSelectionModel().getSelectedItem();
            if (sel != null) runAsync(() -> { api.publishAlert(sel.id.get(), "Published in JavaFX"); refreshAllData(); });
        });
        rejBtn.setOnAction(e -> {
            AlertRow sel = table.getSelectionModel().getSelectedItem();
            if (sel != null) runAsync(() -> { api.rejectAlert(sel.id.get(), "Rejected in JavaFX"); refreshAllData(); });
        });
        delBtn.setOnAction(e -> {
            AlertRow sel = table.getSelectionModel().getSelectedItem();
            if (sel != null) runAsync(() -> {
                String d = api.getAlertDeliveries(sel.id.get());
                Platform.runLater(() -> alertDeliveriesArea.setText(d));
            });
        });

        HBox actions = new HBox(10, appBtn, pubBtn, rejBtn, delBtn);
        VBox box = new VBox(12, actions, table, alertDeliveriesArea);
        box.setPadding(new Insets(16));
        return new Tab("Alert Management Centre", box);
    }

    private Tab buildReportsAndAuditTab() {
        ComboBox<String> stateBox = new ComboBox<>(FXCollections.observableArrayList(
                "", "meghalaya", "sikkim", "assam", "arunachal_pradesh", "manipur", "mizoram", "nagaland", "tripura"
        ));
        stateBox.setPromptText("All NE India States");
        Button genBtn = new Button("Generate Situation Report");
        genBtn.setStyle("-fx-background-color: #38bdf8; -fx-text-fill: #0f172a; -fx-font-weight: bold;");

        reportArea = new TextArea("Click 'Generate Situation Report' after login.");
        reportArea.setEditable(false);
        reportArea.setPrefHeight(280);

        auditArea = new TextArea("Audit logs will appear after login.");
        auditArea.setEditable(false);
        auditArea.setPrefHeight(220);

        genBtn.setOnAction(e -> runAsync(() -> {
            String rep = api.generateSituationReport(stateBox.getValue());
            String aud = api.getAuditLogs();
            Platform.runLater(() -> {
                reportArea.setText(rep);
                auditArea.setText(aud);
            });
        }));

        VBox box = new VBox(10,
                new HBox(10, stateBox, genBtn),
                new Label("Situation Report JSON:") {{ setStyle("-fx-text-fill: #cbd5e1;"); }}, reportArea,
                new Label("Administrative Audit Logs:") {{ setStyle("-fx-text-fill: #cbd5e1;"); }}, auditArea
        );
        box.setPadding(new Insets(16));
        return new Tab("Situation Reports & Audit", box);
    }

    private Tab buildAgentTab() {
        agentChatArea = new TextArea("GeoSense AI Decision-Support Agent ready.\n");
        agentChatArea.setEditable(false);
        agentChatArea.setPrefHeight(480);

        TextField input = new TextField();
        input.setPromptText("Ask e.g. 'Generate a situation report for Meghalaya' or 'What is the landslide risk in Shillong?'");
        HBox.setHgrow(input, Priority.ALWAYS);
        Button sendBtn = new Button("Ask Agent");
        sendBtn.setStyle("-fx-background-color: #38bdf8; -fx-text-fill: #0f172a; -fx-font-weight: bold;");

        sendBtn.setOnAction(e -> {
            String q = input.getText().trim();
            if (q.isEmpty()) return;
            input.clear();
            agentChatArea.appendText("\nAuthority: " + q + "\n");
            runAsync(() -> {
                String resp = api.askAgent(q);
                String reply = ApiClient.extractJsonString(resp, "reply");
                Platform.runLater(() -> agentChatArea.appendText("GeoSense Agent: " + reply + "\n"));
            });
        });

        VBox box = new VBox(12, agentChatArea, new HBox(10, input, sendBtn));
        box.setPadding(new Insets(16));
        return new Tab("AI Decision-Support Agent", box);
    }

    private void refreshAllData() throws Exception {
        String dash = api.getAuthorityDashboard();
        String incsJson = api.getAuthorityIncidents();
        String resJson = api.getResources();
        String alertsJson = api.getAlerts();
        String audJson = api.getAuditLogs();

        List<String> incObjs = ApiClient.splitJsonObjectsInArray(incsJson, "incidents");
        List<String> resObjs = ApiClient.splitJsonObjectsInArray(resJson, "resources");
        List<String> alertObjs = ApiClient.splitJsonObjectsInArray(alertsJson, "alerts");

        Platform.runLater(() -> {
            kpiRiskLocs.setText(ApiClient.extractJsonNumber(dash, "total_risk_assessments"));
            int high = Integer.parseInt(ApiClient.extractJsonNumber(dash, "high_risk_locations"));
            int crit = Integer.parseInt(ApiClient.extractJsonNumber(dash, "critical_risk_locations"));
            kpiHighCrit.setText(String.valueOf(high + crit));
            kpiPendingInc.setText(ApiClient.extractJsonNumber(dash, "pending"));
            kpiVerifiedRes.setText(ApiClient.extractJsonNumber(dash, "verified_resources"));
            kpiInspections.setText(ApiClient.extractJsonNumber(dash, "available_detection_features"));

            incidentRows.clear();
            for (String obj : incObjs) {
                incidentRows.add(new IncidentRow(
                        ApiClient.extractJsonString(obj, "id"),
                        ApiClient.extractJsonString(obj, "incident_category"),
                        ApiClient.extractJsonString(obj, "state"),
                        ApiClient.extractJsonString(obj, "status"),
                        ApiClient.extractJsonString(obj, "description")
                ));
            }

            resourceRows.clear();
            for (String obj : resObjs) {
                resourceRows.add(new ResourceRow(
                        ApiClient.extractJsonString(obj, "resource_id"),
                        ApiClient.extractJsonString(obj, "resource_name"),
                        ApiClient.extractJsonString(obj, "resource_type"),
                        ApiClient.extractJsonString(obj, "verification_status"),
                        ApiClient.extractJsonString(obj, "operational_status"),
                        ApiClient.extractJsonString(obj, "availability_status")
                ));
            }

            alertRows.clear();
            for (String obj : alertObjs) {
                alertRows.add(new AlertRow(
                        ApiClient.extractJsonString(obj, "alert_id"),
                        ApiClient.extractJsonString(obj, "severity"),
                        ApiClient.extractJsonString(obj, "title"),
                        ApiClient.extractJsonString(obj, "state"),
                        ApiClient.extractJsonString(obj, "approval_status")
                ));
            }

            if (auditArea != null) {
                auditArea.setText(audJson);
            }
        });
    }

    private void runAsync(ThrowingRunnable task) {
        new Thread(() -> {
            try {
                task.run();
            } catch (Exception ex) {
                Platform.runLater(() -> authStatusLabel.setText("Error: " + ex.getMessage()));
            }
        }).start();
    }

    private Label makeKpiLabel(String text) {
        Label l = new Label(text);
        l.setStyle("-fx-text-fill: #f8fafc; -fx-font-size: 24px; -fx-font-weight: bold;");
        return l;
    }

    private VBox makeKpiCard(String title, Label val) {
        Label t = new Label(title);
        t.setStyle("-fx-text-fill: #94a3b8; -fx-font-size: 11px;");
        VBox card = new VBox(4, t, val);
        card.setPrefWidth(200);
        card.setPadding(new Insets(12));
        card.setStyle("-fx-background-color: #1e293b; -fx-border-color: #334155; -fx-background-radius: 8; -fx-border-radius: 8;");
        return card;
    }

    @FunctionalInterface
    interface ThrowingRunnable {
        void run() throws Exception;
    }

    public static class IncidentRow {
        final SimpleStringProperty id, category, state, status, description;
        IncidentRow(String id, String category, String state, String status, String description) {
            this.id = new SimpleStringProperty(id);
            this.category = new SimpleStringProperty(category);
            this.state = new SimpleStringProperty(state);
            this.status = new SimpleStringProperty(status);
            this.description = new SimpleStringProperty(description);
        }
    }

    public static class ResourceRow {
        final SimpleStringProperty id, name, type, verification, operational, availability;
        ResourceRow(String id, String name, String type, String verification, String operational, String availability) {
            this.id = new SimpleStringProperty(id);
            this.name = new SimpleStringProperty(name);
            this.type = new SimpleStringProperty(type);
            this.verification = new SimpleStringProperty(verification);
            this.operational = new SimpleStringProperty(operational);
            this.availability = new SimpleStringProperty(availability);
        }
    }

    public static class AlertRow {
        final SimpleStringProperty id, severity, title, state, status;
        AlertRow(String id, String severity, String title, String state, String status) {
            this.id = new SimpleStringProperty(id);
            this.severity = new SimpleStringProperty(severity);
            this.title = new SimpleStringProperty(title);
            this.state = new SimpleStringProperty(state);
            this.status = new SimpleStringProperty(status);
        }
    }

    public static void main(String[] args) {
        launch(args);
    }
}
