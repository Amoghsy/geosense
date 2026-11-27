package com.geosense.authority;

import javafx.application.Application;
import javafx.application.Platform;
import javafx.beans.property.SimpleStringProperty;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Node;
import javafx.scene.Scene;
import javafx.scene.canvas.Canvas;
import javafx.scene.canvas.GraphicsContext;
import javafx.scene.chart.*;
import javafx.scene.control.*;
import javafx.scene.layout.*;
import javafx.scene.paint.Color;
import javafx.scene.shape.Arc;
import javafx.scene.shape.ArcType;
import javafx.scene.shape.Circle;
import javafx.scene.shape.StrokeLineCap;
import javafx.stage.Stage;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

/**
 * GeoSense — Authority Command Center (JavaFX Desktop Application).
 * Implements the 9-screen Emerald Forest & Mint-White UI/UX from GeoSense Desktop UIUX.pdf,
 * connected to the GeoSense FastAPI Backend (Phases 1-9).
 */
public class GeoSenseAuthorityApp extends Application {

    private static final String EMERALD_DARK = "#053324";
    private static final String EMERALD_MID = "#0A4F38";
    private static final String EMERALD_ACTIVE = "#0D8A5E";
    private static final String BG_CANVAS = "#F4F7F5";
    private static final String CARD_STYLE = "-fx-background-color: #FFFFFF; -fx-background-radius: 12; -fx-border-color: #E2E8F0; -fx-border-radius: 12; -fx-padding: 16;";
    private static final String BTN_PRIMARY = "-fx-background-color: #0D8A5E; -fx-text-fill: #FFFFFF; -fx-font-weight: bold; -fx-background-radius: 8; -fx-padding: 8 14; cursor: hand;";
    private static final String BTN_SECONDARY = "-fx-background-color: #FFFFFF; -fx-text-fill: #0F172A; -fx-border-color: #CBD5E1; -fx-border-radius: 8; -fx-background-radius: 8; -fx-padding: 7 12; cursor: hand;";
    private static final String BTN_DANGER = "-fx-background-color: #FEE2E2; -fx-text-fill: #DC2626; -fx-font-weight: bold; -fx-background-radius: 8; -fx-padding: 8 14; cursor: hand;";

    private final ApiClient api = new ApiClient("http://localhost:8000");

    private final StackPane contentHost = new StackPane();
    private final Map<String, Button> navButtons = new LinkedHashMap<>();
    private final Map<String, Node> pages = new LinkedHashMap<>();

    private Label headerTitle;
    private Label headerSubtitle;
    private Label syncLabel;
    private Label userAvatarLabel;
    private Label userNameLabel;
    private Label userRoleLabel;
    private Label incidentBadge;

    // Live bound KPI & detail nodes
    private Label kpiHighRisk = new Label("0");
    private Label kpiModRisk = new Label("0");
    private Label kpiLowRisk = new Label("0");
    private Label kpiActiveInc = new Label("0");
    private Label kpiShelters = new Label("0");
    private Label gaugeScoreLabel = new Label("--");
    private Arc gaugeArc = new Arc(46, 46, 38, 38, 90, 0);
    private Label xaiWhyLabel = new Label("Connect and run prediction to view live Phase 5 XAI explanation.");
    private Label rain24Label = new Label("-- mm");
    private Label slopeLabel = new Label("--");
    private Canvas dashMapCanvas = new Canvas(480, 260);
    private Canvas monitorMapCanvas = new Canvas(520, 260);

    private final ObservableList<IncidentRow> incidentRows = FXCollections.observableArrayList();
    private final ObservableList<ResourceRow> resourceRows = FXCollections.observableArrayList();
    private final ObservableList<AlertRow> alertRows = FXCollections.observableArrayList();
    private final ObservableList<InspectionRow> inspectionRows = FXCollections.observableArrayList();

    private VBox recentIncidentsBox = new VBox(10);
    private TextArea reportPreviewArea = new TextArea();
    private TextArea auditLogArea = new TextArea();
    private TextArea deliveryTrackArea = new TextArea();
    private TextArea agentChatArea = new TextArea();
    private Label channelStatusLabel = new Label("Email: Checking... | FCM: Checking...");

    private LineChart<String, Number> riskTrendChart;
    private BarChart<String, Number> stateBarChart;

    @Override
    public void start(Stage stage) {
        stage.setTitle("GeoSense — Authority Command Center");

        BorderPane root = new BorderPane();
        root.setStyle("-fx-background-color: " + BG_CANVAS + "; -fx-font-family: 'Segoe UI', system-ui, sans-serif;");

        root.setLeft(buildSidebar(stage));

        BorderPane mainShell = new BorderPane();
        mainShell.setTop(buildTopBanner(stage));

        ScrollPane scroll = new ScrollPane(contentHost);
        scroll.setFitToWidth(true);
        scroll.setStyle("-fx-background: " + BG_CANVAS + "; -fx-background-color: " + BG_CANVAS + ";");
        contentHost.setPadding(new Insets(20));
        mainShell.setCenter(scroll);

        root.setCenter(mainShell);

        initPages();
        switchPage("Authority Dashboard", "Real-time landslide intelligence, early warning & coordinated response");

        Scene scene = new Scene(root, 1360, 820);
        stage.setScene(scene);
        stage.show();

        // Prompt login or auto-check channel status
        runAsync(() -> {
            String ch = api.getChannelStatus();
            Platform.runLater(() -> channelStatusLabel.setText("Channels: " + ch));
        });
    }

    private VBox buildSidebar(Stage stage) {
        VBox sidebar = new VBox(6);
        sidebar.setPrefWidth(245);
        sidebar.setPadding(new Insets(18, 14, 16, 14));
        sidebar.setStyle("-fx-background-color: " + EMERALD_DARK + ";");

        Label brand = new Label("GeoSense");
        brand.setStyle("-fx-text-fill: #FFFFFF; -fx-font-size: 20px; -fx-font-weight: bold;");
        Label subBrand = new Label("AUTHORITY COMMAND CENTER");
        subBrand.setStyle("-fx-text-fill: #86EFAC; -fx-font-size: 10px; -fx-font-weight: bold;");
        VBox brandBox = new VBox(2, brand, subBrand);
        brandBox.setPadding(new Insets(0, 4, 16, 4));

        Label secLbl = new Label("OPERATIONS WORKSPACE");
        secLbl.setStyle("-fx-text-fill: #6EE7B7; -fx-font-size: 10px; -fx-font-weight: bold; -fx-padding: 4 8 6 8;");

        sidebar.getChildren().addAll(brandBox, secLbl);

        String[][] navItems = {
                {"Authority Dashboard", "Real-time landslide intelligence, early warning & coordinated response"},
                {"Risk Monitoring", "Spatial risk surveillance, rainfall overlays & sensor network intelligence"},
                {"Prediction & Analysis", "Explainable AI assessments to turn environmental signals into early action"},
                {"Incident Management", "Verify ground reports, prioritize response & track incidents to resolution"},
                {"Field Operations", "Coordinate field officers, deploy response teams & monitor inspections"},
                {"Resources & Shelter", "Maintain shelter readiness, verify medical assets & coordinate relief"},
                {"Alerts & Communication", "Review risk alerts, approve public advisories & track Email + FCM delivery"},
                {"Reports & Analytics", "Evaluate district exposure, response outcomes & generate situation reports"},
                {"System Administration", "Govern access, configure AI thresholds & inspect audit logs"}
        };

        incidentBadge = new Label("0");
        incidentBadge.setStyle("-fx-background-color: #EF4444; -fx-text-fill: white; -fx-font-size: 10px; -fx-font-weight: bold; -fx-padding: 1 6; -fx-background-radius: 10;");

        for (String[] item : navItems) {
            String title = item[0];
            String sub = item[1];
            Button btn = new Button(title);
            btn.setMaxWidth(Double.MAX_VALUE);
            btn.setAlignment(Pos.CENTER_LEFT);
            btn.setOnAction(e -> switchPage(title, sub));
            navButtons.put(title, btn);

            if ("Incident Management".equals(title)) {
                HBox row = new HBox(btn, incidentBadge);
                HBox.setHgrow(btn, Priority.ALWAYS);
                row.setAlignment(Pos.CENTER_LEFT);
                sidebar.getChildren().add(row);
            } else {
                sidebar.getChildren().add(btn);
            }
        }

        Region spacer = new Region();
        VBox.setVgrow(spacer, Priority.ALWAYS);

        Label opsDot = new Label("● All systems operational");
        opsDot.setStyle("-fx-text-fill: #34D399; -fx-font-size: 11px; -fx-font-weight: bold;");
        syncLabel = new Label("Last sync: Not connected");
        syncLabel.setStyle("-fx-text-fill: #A7F3D0; -fx-font-size: 10px;");
        Label tagline = new Label("Predict Early. Monitor Continuously.\nRespond Intelligently. Save Lives.");
        tagline.setStyle("-fx-text-fill: #6EE7B7; -fx-font-size: 10px; -fx-padding: 8 0 0 0;");

        VBox footer = new VBox(4, opsDot, syncLabel, tagline);
        footer.setPadding(new Insets(12, 8, 4, 8));
        footer.setStyle("-fx-background-color: #04281C; -fx-background-radius: 8;");

        sidebar.getChildren().addAll(spacer, footer);
        return sidebar;
    }

    private HBox buildTopBanner(Stage stage) {
        Label stateTop = new Label("NORTH EASTERN REGION / STATE DISASTER MANAGEMENT AUTHORITY");
        stateTop.setStyle("-fx-text-fill: #A7F3D0; -fx-font-size: 10px; -fx-font-weight: bold;");
        headerTitle = new Label("Authority Dashboard");
        headerTitle.setStyle("-fx-text-fill: #FFFFFF; -fx-font-size: 22px; -fx-font-weight: bold;");
        headerSubtitle = new Label("Real-time landslide intelligence, early warning & coordinated response");
        headerSubtitle.setStyle("-fx-text-fill: #D1FAE5; -fx-font-size: 12px;");
        VBox left = new VBox(2, stateTop, headerTitle, headerSubtitle);

        Region spacer = new Region();
        HBox.setHgrow(spacer, Priority.ALWAYS);

        Label clock = new Label(LocalDateTime.now().format(DateTimeFormatter.ofPattern("dd MMM yyyy · HH:mm")));
        clock.setStyle("-fx-text-fill: #FFFFFF; -fx-font-weight: bold; -fx-font-size: 12px;");
        Label livePill = new Label("● LIVE");
        livePill.setStyle("-fx-background-color: #10B981; -fx-text-fill: #FFFFFF; -fx-font-size: 10px; -fx-font-weight: bold; -fx-padding: 4 10; -fx-background-radius: 12;");

        Button connectBtn = new Button("Connect / Login");
        connectBtn.setStyle("-fx-background-color: #FFFFFF; -fx-text-fill: #053324; -fx-font-weight: bold; -fx-background-radius: 8; -fx-padding: 6 12;");
        connectBtn.setOnAction(e -> showAuthDialog());

        userAvatarLabel = new Label("AK");
        userAvatarLabel.setStyle("-fx-background-color: #0D8A5E; -fx-text-fill: #FFFFFF; -fx-font-weight: bold; -fx-padding: 8 10; -fx-background-radius: 20;");
        userNameLabel = new Label("Sign In");
        userNameLabel.setStyle("-fx-text-fill: #FFFFFF; -fx-font-weight: bold; -fx-font-size: 12px;");
        userRoleLabel = new Label("Authority");
        userRoleLabel.setStyle("-fx-text-fill: #A7F3D0; -fx-font-size: 10px;");
        VBox userInfo = new VBox(1, userNameLabel, userRoleLabel);

        HBox right = new HBox(12, clock, livePill, connectBtn, userAvatarLabel, userInfo);
        right.setAlignment(Pos.CENTER_RIGHT);

        HBox banner = new HBox(16, left, spacer, right);
        banner.setAlignment(Pos.CENTER_LEFT);
        banner.setPadding(new Insets(14, 22, 14, 22));
        banner.setStyle("-fx-background-color: linear-gradient(to right, " + EMERALD_DARK + ", " + EMERALD_MID + ");");
        return banner;
    }

    private void switchPage(String name, String subtitle) {
        headerTitle.setText(name);
        headerSubtitle.setText(subtitle);
        for (Map.Entry<String, Button> e : navButtons.entrySet()) {
            boolean active = e.getKey().equals(name);
            e.getValue().setStyle(active
                    ? "-fx-background-color: " + EMERALD_ACTIVE + "; -fx-text-fill: #FFFFFF; -fx-font-weight: bold; -fx-background-radius: 8; -fx-padding: 10 12;"
                    : "-fx-background-color: transparent; -fx-text-fill: #D1FAE5; -fx-background-radius: 8; -fx-padding: 10 12;");
        }
        contentHost.getChildren().setAll(pages.get(name));
    }

    private void initPages() {
        pages.put("Authority Dashboard", buildDashboardPage());
        pages.put("Risk Monitoring", buildRiskMonitoringPage());
        pages.put("Prediction & Analysis", buildPredictionPage());
        pages.put("Incident Management", buildIncidentsPage());
        pages.put("Field Operations", buildFieldOpsPage());
        pages.put("Resources & Shelter", buildResourcesPage());
        pages.put("Alerts & Communication", buildAlertsPage());
        pages.put("Reports & Analytics", buildReportsPage());
        pages.put("System Administration", buildAdminPage());
    }

    // =========================================================
    // PAGE 1: AUTHORITY DASHBOARD
    // =========================================================
    private Node buildDashboardPage() {
        HBox kpis = new HBox(12,
                makeKpiCard("High / Critical risk", kpiHighRisk, "#DC2626", "Active hotspots"),
                makeKpiCard("Moderate risk locations", kpiModRisk, "#D97706", "Monitored points"),
                makeKpiCard("Low risk locations", kpiLowRisk, "#059669", "Baseline locations"),
                makeKpiCard("Active incidents", kpiActiveInc, "#EA580C", "Citizen + Officer"),
                makeKpiCard("Verified shelters & assets", kpiShelters, "#0D8A5E", "Phase 7 verified")
        );

        // Left: GIS Map Card
        VBox mapCard = new VBox(10);
        mapCard.setStyle(CARD_STYLE);
        HBox.setHgrow(mapCard, Priority.ALWAYS);
        Label mTitle = new Label("Landslide risk map");
        mTitle.setStyle("-fx-font-size: 15px; -fx-font-weight: bold; -fx-text-fill: #0F172A;");
        Label mSub = new Label("North Eastern India • Regional risk zones & verified hotspots (EPSG:4326)");
        mSub.setStyle("-fx-font-size: 11px; -fx-text-fill: #64748B;");
        drawMapCanvas(dashMapCanvas, new ArrayList<>());
        Label legend = new Label("● High/Critical   ● Moderate   ● Low   (Provisional heuristic index, not calibrated probability)");
        legend.setStyle("-fx-font-size: 11px; -fx-text-fill: #64748B;");
        mapCard.getChildren().addAll(mTitle, mSub, dashMapCanvas, legend);

        // Right: AI Risk Prediction Card (with circular gauge + XAI box)
        VBox aiCard = new VBox(12);
        aiCard.setPrefWidth(390);
        aiCard.setStyle(CARD_STYLE);
        Label aTitle = new Label("AI risk index (Phase 3 + 5)");
        aTitle.setStyle("-fx-font-size: 15px; -fx-font-weight: bold; -fx-text-fill: #0F172A;");

        Circle bgCircle = new Circle(46, 46, 38);
        bgCircle.setFill(Color.TRANSPARENT);
        bgCircle.setStroke(Color.web("#E2E8F0"));
        bgCircle.setStrokeWidth(8);
        gaugeArc.setFill(Color.TRANSPARENT);
        gaugeArc.setStroke(Color.web("#DC2626"));
        gaugeArc.setStrokeWidth(8);
        gaugeArc.setStrokeLineCap(StrokeLineCap.ROUND);
        gaugeArc.setType(ArcType.OPEN);
        gaugeScoreLabel.setStyle("-fx-font-size: 22px; -fx-font-weight: bold; -fx-text-fill: #0F172A;");
        StackPane gaugePane = new StackPane(new Pane(bgCircle, gaugeArc), gaugeScoreLabel);
        gaugePane.setPrefSize(96, 96);

        VBox statsCol = new VBox(6,
                new HBox(8, new Label("Rainfall / 24h:") {{ setStyle("-fx-text-fill:#64748B;"); }}, rain24Label),
                new HBox(8, new Label("Slope / Elevation:") {{ setStyle("-fx-text-fill:#64748B;"); }}, slopeLabel)
        );
        HBox gaugeRow = new HBox(16, gaugePane, statsCol);
        gaugeRow.setAlignment(Pos.CENTER_LEFT);

        VBox whyBox = new VBox(4,
                new Label("WHY THIS RISK INDEX?") {{ setStyle("-fx-text-fill:#B45309; -fx-font-weight:bold; -fx-font-size:11px;"); }},
                xaiWhyLabel
        );
        xaiWhyLabel.setWrapText(true);
        xaiWhyLabel.setStyle("-fx-text-fill: #78350F; -fx-font-size: 12px;");
        whyBox.setStyle("-fx-background-color: #FEF3C7; -fx-background-radius: 8; -fx-padding: 10;");

        Button runBtn = new Button("Assess Shillong (Live Open-Meteo)");
        runBtn.setStyle(BTN_PRIMARY);
        runBtn.setOnAction(e -> runAsync(() -> {
            String res = api.analyzeRisk(25.5788, 91.8933, "Shillong, Meghalaya", 1496, 28);
            double score = Double.parseDouble(ApiClient.extractJsonNumber(res, "risk_score"));
            String explain = ApiClient.extractJsonString(res, "explanation");
            String r24 = ApiClient.extractJsonNumber(res, "rainfall_mm");
            Platform.runLater(() -> {
                gaugeScoreLabel.setText(String.format("%.0f", score));
                gaugeArc.setLength(-(score / 100.0) * 360.0);
                rain24Label.setText(r24 + " mm");
                slopeLabel.setText("28° / 1496 m");
                xaiWhyLabel.setText(explain);
            });
            refreshAllData();
        }));
        aiCard.getChildren().addAll(aTitle, gaugeRow, whyBox, runBtn);

        HBox middleRow = new HBox(16, mapCard, aiCard);

        // Bottom 3 cards: Trend Chart, Recent Incidents, Quick Actions
        CategoryAxis xAx = new CategoryAxis();
        NumberAxis yAx = new NumberAxis(0, 100, 25);
        riskTrendChart = new LineChart<>(xAx, yAx);
        riskTrendChart.setPrefHeight(200);
        riskTrendChart.setLegendVisible(false);
        VBox trendCard = new VBox(8, new Label("Risk trend") {{ setStyle("-fx-font-weight:bold; -fx-font-size:14px;"); }}, riskTrendChart);
        trendCard.setStyle(CARD_STYLE);
        HBox.setHgrow(trendCard, Priority.ALWAYS);

        VBox recentCard = new VBox(8, new Label("Recent incidents") {{ setStyle("-fx-font-weight:bold; -fx-font-size:14px;"); }}, recentIncidentsBox);
        recentCard.setStyle(CARD_STYLE);
        recentCard.setPrefWidth(340);

        Button qaWarn = new Button("Issue warning"); qaWarn.setStyle(BTN_SECONDARY);
        qaWarn.setOnAction(e -> switchPage("Alerts & Communication", "Review risk alerts, approve public advisories & track Email + FCM delivery"));
        Button qaOps = new Button("Deploy officer"); qaOps.setStyle(BTN_SECONDARY);
        qaOps.setOnAction(e -> switchPage("Field Operations", "Coordinate field officers, deploy response teams & monitor inspections"));
        Button qaRes = new Button("Allocate relief"); qaRes.setStyle(BTN_SECONDARY);
        qaRes.setOnAction(e -> switchPage("Resources & Shelter", "Maintain shelter readiness, verify medical assets & coordinate relief"));
        Button qaRep = new Button("Generate report"); qaRep.setStyle(BTN_PRIMARY);
        qaRep.setOnAction(e -> switchPage("Reports & Analytics", "Evaluate district exposure, response outcomes & generate situation reports"));

        GridPane qaGrid = new GridPane();
        qaGrid.setHgap(8); qaGrid.setVgap(8);
        qaGrid.add(qaWarn, 0, 0); qaGrid.add(qaOps, 1, 0);
        qaGrid.add(qaRes, 0, 1); qaGrid.add(qaRep, 1, 1);
        VBox qaCard = new VBox(10, new Label("Quick actions") {{ setStyle("-fx-font-weight:bold; -fx-font-size:14px;"); }}, qaGrid);
        qaCard.setStyle(CARD_STYLE);
        qaCard.setPrefWidth(280);

        HBox bottomRow = new HBox(16, trendCard, recentCard, qaCard);
        return new VBox(16, kpis, middleRow, bottomRow);
    }

    // =========================================================
    // PAGE 2: RISK MONITORING
    // =========================================================
    private Node buildRiskMonitoringPage() {
        VBox card = new VBox(12);
        card.setStyle(CARD_STYLE);
        Label t = new Label("Terrain & monitoring network (Phase 3 + Phase 4 GIS)");
        t.setStyle("-fx-font-size: 15px; -fx-font-weight: bold;");
        drawMapCanvas(monitorMapCanvas, new ArrayList<>());
        Button refreshMap = new Button("Refresh GIS Hotspots");
        refreshMap.setStyle(BTN_PRIMARY);
        refreshMap.setOnAction(e -> runAsync(this::refreshAllData));
        card.getChildren().addAll(t, monitorMapCanvas, refreshMap);
        return card;
    }

    // =========================================================
    // PAGE 3: PREDICTION & ANALYSIS (XAI + AI AGENT)
    // =========================================================
    private Node buildPredictionPage() {
        VBox card = new VBox(12);
        card.setStyle(CARD_STYLE);
        Label t = new Label("Explainable AI & Decision-Support Agent (Phases 5 & 6)");
        t.setStyle("-fx-font-size: 15px; -fx-font-weight: bold;");

        agentChatArea.setEditable(false);
        agentChatArea.setPrefHeight(360);
        agentChatArea.setText("GeoSense Decision-Support Agent ready.\nAsk about risk explanations, rainfall, hotspots, or verified resources.\n");

        TextField input = new TextField();
        input.setPromptText("Ask e.g. 'Why is Shillong at its current risk level?'");
        HBox.setHgrow(input, Priority.ALWAYS);
        Button send = new Button("Ask Agent");
        send.setStyle(BTN_PRIMARY);
        send.setOnAction(e -> {
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

        card.getChildren().addAll(t, agentChatArea, new HBox(10, input, send));
        return card;
    }

    // =========================================================
    // PAGE 4: INCIDENT MANAGEMENT
    // =========================================================
    private Node buildIncidentsPage() {
        TableView<IncidentRow> table = new TableView<>(incidentRows);
        table.setPrefHeight(420);
        TableColumn<IncidentRow, String> c1 = new TableColumn<>("ID"); c1.setCellValueFactory(d -> d.getValue().id);
        TableColumn<IncidentRow, String> c2 = new TableColumn<>("Category"); c2.setCellValueFactory(d -> d.getValue().category);
        TableColumn<IncidentRow, String> c3 = new TableColumn<>("State"); c3.setCellValueFactory(d -> d.getValue().state);
        TableColumn<IncidentRow, String> c4 = new TableColumn<>("Verification"); c4.setCellValueFactory(d -> d.getValue().status);
        TableColumn<IncidentRow, String> c5 = new TableColumn<>("Description"); c5.setCellValueFactory(d -> d.getValue().description); c5.setPrefWidth(420);
        table.getColumns().addAll(c1, c2, c3, c4, c5);

        Button verifyBtn = new Button("Verify incident"); verifyBtn.setStyle(BTN_PRIMARY);
        Button rejectBtn = new Button("Reject report"); rejectBtn.setStyle(BTN_DANGER);
        verifyBtn.setOnAction(e -> {
            IncidentRow sel = table.getSelectionModel().getSelectedItem();
            if (sel != null) runAsync(() -> { api.verifyIncident(sel.id.get(), "VERIFIED", "Verified in Authority Command Center"); refreshAllData(); });
        });
        rejectBtn.setOnAction(e -> {
            IncidentRow sel = table.getSelectionModel().getSelectedItem();
            if (sel != null) runAsync(() -> { api.verifyIncident(sel.id.get(), "REJECTED", "Rejected in Authority Command Center"); refreshAllData(); });
        });

        VBox card = new VBox(12, new HBox(10, verifyBtn, rejectBtn), table);
        card.setStyle(CARD_STYLE);
        return card;
    }

    // =========================================================
    // PAGE 5: FIELD OPERATIONS
    // =========================================================
    private Node buildFieldOpsPage() {
        TableView<InspectionRow> table = new TableView<>(inspectionRows);
        table.setPrefHeight(440);
        TableColumn<InspectionRow, String> c1 = new TableColumn<>("Inspection ID"); c1.setCellValueFactory(d -> d.getValue().id);
        TableColumn<InspectionRow, String> c2 = new TableColumn<>("Officer"); c2.setCellValueFactory(d -> d.getValue().officerId);
        TableColumn<InspectionRow, String> c3 = new TableColumn<>("State"); c3.setCellValueFactory(d -> d.getValue().state);
        TableColumn<InspectionRow, String> c4 = new TableColumn<>("Status"); c4.setCellValueFactory(d -> d.getValue().status);
        TableColumn<InspectionRow, String> c5 = new TableColumn<>("Observations"); c5.setCellValueFactory(d -> d.getValue().observations); c5.setPrefWidth(420);
        table.getColumns().addAll(c1, c2, c3, c4, c5);

        VBox card = new VBox(12, new Label("Field inspections & assignments") {{ setStyle("-fx-font-weight:bold; -fx-font-size:15px;"); }}, table);
        card.setStyle(CARD_STYLE);
        return card;
    }

    // =========================================================
    // PAGE 6: RESOURCES & SHELTER
    // =========================================================
    private Node buildResourcesPage() {
        TableView<ResourceRow> table = new TableView<>(resourceRows);
        table.setPrefHeight(360);
        TableColumn<ResourceRow, String> c1 = new TableColumn<>("ID"); c1.setCellValueFactory(d -> d.getValue().id);
        TableColumn<ResourceRow, String> c2 = new TableColumn<>("Facility"); c2.setCellValueFactory(d -> d.getValue().name); c2.setPrefWidth(220);
        TableColumn<ResourceRow, String> c3 = new TableColumn<>("Type"); c3.setCellValueFactory(d -> d.getValue().type);
        TableColumn<ResourceRow, String> c4 = new TableColumn<>("Verification"); c4.setCellValueFactory(d -> d.getValue().verification);
        TableColumn<ResourceRow, String> c5 = new TableColumn<>("Operational"); c5.setCellValueFactory(d -> d.getValue().operational);
        TableColumn<ResourceRow, String> c6 = new TableColumn<>("Availability"); c6.setCellValueFactory(d -> d.getValue().availability);
        table.getColumns().addAll(c1, c2, c3, c4, c5, c6);

        Button verBtn = new Button("Verify resource"); verBtn.setStyle(BTN_PRIMARY);
        Button rejBtn = new Button("Reject resource"); rejBtn.setStyle(BTN_DANGER);
        verBtn.setOnAction(e -> {
            ResourceRow sel = table.getSelectionModel().getSelectedItem();
            if (sel != null) runAsync(() -> { api.verifyResource(sel.id.get(), "VERIFIED"); refreshAllData(); });
        });
        rejBtn.setOnAction(e -> {
            ResourceRow sel = table.getSelectionModel().getSelectedItem();
            if (sel != null) runAsync(() -> { api.verifyResource(sel.id.get(), "REJECTED"); refreshAllData(); });
        });

        TextField rName = new TextField(); rName.setPromptText("Facility name");
        ComboBox<String> rType = new ComboBox<>(FXCollections.observableArrayList("HOSPITAL", "SHELTER", "AMBULANCE", "RESCUE_TEAM", "FIRE_STATION"));
        rType.setValue("SHELTER");
        TextField rState = new TextField("Meghalaya");
        Button addBtn = new Button("Add candidate (PENDING)"); addBtn.setStyle(BTN_SECONDARY);
        addBtn.setOnAction(e -> {
            if (!rName.getText().isBlank()) runAsync(() -> {
                api.createResource(rName.getText().trim(), rType.getValue(), rState.getText().trim(), 25.5788, 91.8933);
                Platform.runLater(rName::clear);
                refreshAllData();
            });
        });

        VBox card = new VBox(12, new HBox(10, verBtn, rejBtn), table, new HBox(10, rName, rType, rState, addBtn));
        card.setStyle(CARD_STYLE);
        return card;
    }

    // =========================================================
    // PAGE 7: ALERTS & COMMUNICATION (EMAIL + FCM ONLY — NO SMS)
    // =========================================================
    private Node buildAlertsPage() {
        TableView<AlertRow> table = new TableView<>(alertRows);
        table.setPrefHeight(280);
        TableColumn<AlertRow, String> c1 = new TableColumn<>("Alert ID"); c1.setCellValueFactory(d -> d.getValue().id);
        TableColumn<AlertRow, String> c2 = new TableColumn<>("Severity"); c2.setCellValueFactory(d -> d.getValue().severity);
        TableColumn<AlertRow, String> c3 = new TableColumn<>("Headline"); c3.setCellValueFactory(d -> d.getValue().title); c3.setPrefWidth(280);
        TableColumn<AlertRow, String> c4 = new TableColumn<>("State"); c4.setCellValueFactory(d -> d.getValue().state);
        TableColumn<AlertRow, String> c5 = new TableColumn<>("Approval"); c5.setCellValueFactory(d -> d.getValue().status);
        table.getColumns().addAll(c1, c2, c3, c4, c5);

        Button appBtn = new Button("Approve"); appBtn.setStyle(BTN_SECONDARY);
        Button pubBtn = new Button("Publish (Email + FCM Push)"); pubBtn.setStyle(BTN_PRIMARY);
        Button rejBtn = new Button("Reject"); rejBtn.setStyle(BTN_DANGER);
        Button delBtn = new Button("Delivery tracking"); delBtn.setStyle(BTN_SECONDARY);

        appBtn.setOnAction(e -> { AlertRow s = table.getSelectionModel().getSelectedItem(); if (s != null) runAsync(() -> { api.approveAlert(s.id.get(), "Approved"); refreshAllData(); }); });
        pubBtn.setOnAction(e -> { AlertRow s = table.getSelectionModel().getSelectedItem(); if (s != null) runAsync(() -> { api.publishAlert(s.id.get(), "Published via Authority Command"); refreshAllData(); }); });
        rejBtn.setOnAction(e -> { AlertRow s = table.getSelectionModel().getSelectedItem(); if (s != null) runAsync(() -> { api.rejectAlert(s.id.get(), "Rejected"); refreshAllData(); }); });
        delBtn.setOnAction(e -> {
            AlertRow s = table.getSelectionModel().getSelectedItem();
            if (s != null) runAsync(() -> {
                String d = api.getAlertDeliveries(s.id.get());
                Platform.runLater(() -> deliveryTrackArea.setText(d));
            });
        });

        deliveryTrackArea.setEditable(false);
        deliveryTrackArea.setPrefHeight(160);
        deliveryTrackArea.setText("Distribution Channels: Email (SMTP) & Firebase Push (FCM). Select an alert to inspect delivery logs.");

        VBox card = new VBox(12, channelStatusLabel, new HBox(10, appBtn, pubBtn, rejBtn, delBtn), table, deliveryTrackArea);
        card.setStyle(CARD_STYLE);
        return card;
    }

    // =========================================================
    // PAGE 8: REPORTS & ANALYTICS
    // =========================================================
    private Node buildReportsPage() {
        CategoryAxis x = new CategoryAxis();
        NumberAxis y = new NumberAxis();
        stateBarChart = new BarChart<>(x, y);
        stateBarChart.setPrefHeight(240);

        ComboBox<String> stBox = new ComboBox<>(FXCollections.observableArrayList("", "meghalaya", "sikkim", "assam", "arunachal_pradesh"));
        stBox.setValue("");
        Button genBtn = new Button("Generate situation report"); genBtn.setStyle(BTN_PRIMARY);
        reportPreviewArea.setEditable(false);
        reportPreviewArea.setPrefHeight(220);

        genBtn.setOnAction(e -> runAsync(() -> {
            String rep = api.generateSituationReport(stBox.getValue());
            Platform.runLater(() -> reportPreviewArea.setText(rep));
            refreshAllData();
        }));

        VBox card = new VBox(12, new Label("State risk distribution") {{ setStyle("-fx-font-weight:bold; -fx-font-size:15px;"); }},
                stateBarChart, new HBox(10, stBox, genBtn), reportPreviewArea);
        card.setStyle(CARD_STYLE);
        return card;
    }

    // =========================================================
    // PAGE 9: SYSTEM ADMINISTRATION
    // =========================================================
    private Node buildAdminPage() {
        auditLogArea.setEditable(false);
        auditLogArea.setPrefHeight(420);
        auditLogArea.setText("Connect as Authority to load administrative audit logs.");
        VBox card = new VBox(12, new Label("Administrative audit log & system health") {{ setStyle("-fx-font-weight:bold; -fx-font-size:15px;"); }}, auditLogArea);
        card.setStyle(CARD_STYLE);
        return card;
    }

    // =========================================================
    // AUTH DIALOG & LIVE REFRESH
    // =========================================================
    private void showAuthDialog() {
        Dialog<ButtonType> dlg = new Dialog<>();
        dlg.setTitle("GeoSense Authority Authentication");
        TextField urlF = new TextField(api.getBaseUrl());
        TextField emailF = new TextField("authority@geosense.in");
        PasswordField passF = new PasswordField(); passF.setText("Authority@123");
        CheckBox provCb = new CheckBox("Provision new Authority account if first run");
        provCb.setSelected(true);

        GridPane g = new GridPane(); g.setHgap(10); g.setVgap(10); g.setPadding(new Insets(12));
        g.add(new Label("Backend URL:"), 0, 0); g.add(urlF, 1, 0);
        g.add(new Label("Email:"), 0, 1); g.add(emailF, 1, 1);
        g.add(new Label("Password:"), 0, 2); g.add(passF, 1, 2);
        g.add(provCb, 1, 3);
        dlg.getDialogPane().setContent(g);
        dlg.getDialogPane().getButtonTypes().addAll(ButtonType.OK, ButtonType.CANCEL);

        dlg.showAndWait().ifPresent(bt -> {
            if (bt == ButtonType.OK) {
                runAsync(() -> {
                    api.setBaseUrl(urlF.getText().trim());
                    try {
                        api.login(emailF.getText().trim(), passF.getText());
                    } catch (Exception loginEx) {
                        if (provCb.isSelected()) {
                            api.registerAuthority(emailF.getText().trim(), passF.getText(), "A. Kharkongor", "geosense-admin-provision");
                        } else {
                            throw loginEx;
                        }
                    }
                    Platform.runLater(() -> {
                        userNameLabel.setText(emailF.getText().trim());
                        userRoleLabel.setText("Administrator");
                    });
                    refreshAllData();
                });
            }
        });
    }

    private void refreshAllData() throws Exception {
        String dash = api.getAuthorityDashboard();
        String analytics = api.getAuthorityAnalytics();
        String incsJson = api.getAuthorityIncidents();
        String resJson = api.getResources();
        String alertsJson = api.getAlerts();
        String inspJson = api.getInspections();
        String audJson = api.getAuditLogs();
        String hsJson = api.getGisHotspots();

        List<String> incObjs = ApiClient.splitJsonObjectsInArray(incsJson, "incidents");
        List<String> resObjs = ApiClient.splitJsonObjectsInArray(resJson, "resources");
        List<String> alertObjs = ApiClient.splitJsonObjectsInArray(alertsJson, "alerts");
        List<String> inspObjs = ApiClient.splitJsonObjectsInArray(inspJson, "inspections");
        List<String> hsObjs = ApiClient.splitJsonObjectsInArray(hsJson, "hotspots");

        Platform.runLater(() -> {
            int high = Integer.parseInt(ApiClient.extractJsonNumber(dash, "high_risk_locations"));
            int crit = Integer.parseInt(ApiClient.extractJsonNumber(dash, "critical_risk_locations"));
            int totalRisk = Integer.parseInt(ApiClient.extractJsonNumber(dash, "total_risk_assessments"));
            int pendingInc = Integer.parseInt(ApiClient.extractJsonNumber(dash, "pending"));
            kpiHighRisk.setText(String.valueOf(high + crit));
            kpiModRisk.setText(String.valueOf(Math.max(0, totalRisk - high - crit)));
            kpiLowRisk.setText(String.valueOf(totalRisk));
            kpiActiveInc.setText(ApiClient.extractJsonNumber(dash, "total"));
            kpiShelters.setText(ApiClient.extractJsonNumber(dash, "verified_resources"));
            incidentBadge.setText(String.valueOf(pendingInc));
            syncLabel.setText("Last sync: " + LocalDateTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss")));

            incidentRows.clear();
            recentIncidentsBox.getChildren().clear();
            for (int i = 0; i < incObjs.size(); i++) {
                String o = incObjs.get(i);
                IncidentRow row = new IncidentRow(
                        ApiClient.extractJsonString(o, "id"),
                        ApiClient.extractJsonString(o, "incident_category"),
                        ApiClient.extractJsonString(o, "state"),
                        ApiClient.extractJsonString(o, "status"),
                        ApiClient.extractJsonString(o, "description")
                );
                incidentRows.add(row);
                if (i < 3) {
                    Label l = new Label("• " + row.category.get() + " (" + row.status.get() + ") — " + row.state.get());
                    l.setStyle("-fx-font-size: 12px; -fx-text-fill: #334155;");
                    recentIncidentsBox.getChildren().add(l);
                }
            }

            resourceRows.clear();
            for (String o : resObjs) {
                resourceRows.add(new ResourceRow(
                        ApiClient.extractJsonString(o, "resource_id"),
                        ApiClient.extractJsonString(o, "resource_name"),
                        ApiClient.extractJsonString(o, "resource_type"),
                        ApiClient.extractJsonString(o, "verification_status"),
                        ApiClient.extractJsonString(o, "operational_status"),
                        ApiClient.extractJsonString(o, "availability_status")
                ));
            }

            alertRows.clear();
            for (String o : alertObjs) {
                alertRows.add(new AlertRow(
                        ApiClient.extractJsonString(o, "alert_id"),
                        ApiClient.extractJsonString(o, "severity"),
                        ApiClient.extractJsonString(o, "title"),
                        ApiClient.extractJsonString(o, "state"),
                        ApiClient.extractJsonString(o, "approval_status")
                ));
            }

            inspectionRows.clear();
            for (String o : inspObjs) {
                inspectionRows.add(new InspectionRow(
                        ApiClient.extractJsonString(o, "inspection_id"),
                        ApiClient.extractJsonString(o, "officer_id"),
                        ApiClient.extractJsonString(o, "state"),
                        ApiClient.extractJsonString(o, "status"),
                        ApiClient.extractJsonString(o, "observations")
                ));
            }

            drawMapCanvas(dashMapCanvas, hsObjs);
            drawMapCanvas(monitorMapCanvas, hsObjs);
            auditLogArea.setText(audJson);

            // Populate BarChart with real state counts
            stateBarChart.getData().clear();
            XYChart.Series<String, Number> s = new XYChart.Series<>();
            s.setName("Assessed Locations");
            s.getData().add(new XYChart.Data<>("Total", totalRisk));
            s.getData().add(new XYChart.Data<>("High/Crit", high + crit));
            stateBarChart.getData().add(s);
        });
    }

    private void drawMapCanvas(Canvas canvas, List<String> hotspots) {
        GraphicsContext gc = canvas.getGraphicsContext2D();
        double w = canvas.getWidth(), h = canvas.getHeight();
        gc.setFill(Color.web("#E2EAE5"));
        gc.fillRoundRect(0, 0, w, h, 10, 10);

        // Subtle GIS grid lines
        gc.setStroke(Color.web("#CBD5E1"));
        gc.setLineWidth(1);
        for (int x = 40; x < w; x += 60) gc.strokeLine(x, 0, x, h);
        for (int y = 40; y < h; y += 60) gc.strokeLine(0, y, w, y);

        // Illustrative NE India region bounding polygon + Shillong marker
        gc.setFill(Color.web("#9CC5A9", 0.55));
        gc.setStroke(Color.web("#FFFFFF"));
        gc.setLineWidth(2);
        gc.fillPolygon(new double[]{60, 180, 320, 420, 380, 140}, new double[]{140, 80, 70, 130, 210, 200}, 6);
        gc.strokePolygon(new double[]{60, 180, 320, 420, 380, 140}, new double[]{140, 80, 70, 130, 210, 200}, 6);

        gc.setFill(Color.web("#0F172A"));
        gc.fillOval(235, 135, 6, 6);
        gc.fillText("SHILLONG", 245, 142);

        // Plot real hotspots
        gc.setFill(Color.web("#DC2626"));
        for (int i = 0; i < hotspots.size(); i++) {
            double px = 120 + (i * 45) % (w - 160);
            double py = 100 + (i * 30) % (h - 140);
            gc.fillOval(px, py, 12, 12);
        }
    }

    private VBox makeKpiCard(String title, Label valLbl, String accentHex, String sub) {
        Label t = new Label(title);
        t.setStyle("-fx-text-fill: #64748B; -fx-font-size: 12px;");
        valLbl.setStyle("-fx-text-fill: #0F172A; -fx-font-size: 26px; -fx-font-weight: bold;");
        Label s = new Label(sub);
        s.setStyle("-fx-text-fill: " + accentHex + "; -fx-font-size: 11px;");
        VBox card = new VBox(4, t, valLbl, s);
        card.setStyle(CARD_STYLE);
        HBox.setHgrow(card, Priority.ALWAYS);
        return card;
    }

    private void runAsync(ThrowingRunnable r) {
        new Thread(() -> {
            try {
                r.run();
            } catch (Exception ex) {
                Platform.runLater(() -> syncLabel.setText("Err: " + ex.getMessage()));
            }
        }).start();
    }

    @FunctionalInterface
    interface ThrowingRunnable {
        void run() throws Exception;
    }

    public static class IncidentRow {
        final SimpleStringProperty id, category, state, status, description;
        IncidentRow(String id, String category, String state, String status, String description) {
            this.id = new SimpleStringProperty(id); this.category = new SimpleStringProperty(category);
            this.state = new SimpleStringProperty(state); this.status = new SimpleStringProperty(status);
            this.description = new SimpleStringProperty(description);
        }
    }

    public static class ResourceRow {
        final SimpleStringProperty id, name, type, verification, operational, availability;
        ResourceRow(String id, String name, String type, String verification, String operational, String availability) {
            this.id = new SimpleStringProperty(id); this.name = new SimpleStringProperty(name);
            this.type = new SimpleStringProperty(type); this.verification = new SimpleStringProperty(verification);
            this.operational = new SimpleStringProperty(operational); this.availability = new SimpleStringProperty(availability);
        }
    }

    public static class AlertRow {
        final SimpleStringProperty id, severity, title, state, status;
        AlertRow(String id, String severity, String title, String state, String status) {
            this.id = new SimpleStringProperty(id); this.severity = new SimpleStringProperty(severity);
            this.title = new SimpleStringProperty(title); this.state = new SimpleStringProperty(state);
            this.status = new SimpleStringProperty(status);
        }
    }

    public static class InspectionRow {
        final SimpleStringProperty id, officerId, state, status, observations;
        InspectionRow(String id, String officerId, String state, String status, String observations) {
            this.id = new SimpleStringProperty(id); this.officerId = new SimpleStringProperty(officerId);
            this.state = new SimpleStringProperty(state); this.status = new SimpleStringProperty(status);
            this.observations = new SimpleStringProperty(observations);
        }
    }

    public static void main(String[] args) {
        launch(args);
    }
}
