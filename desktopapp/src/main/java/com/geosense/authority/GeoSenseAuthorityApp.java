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
import javafx.scene.image.Image;
import javafx.scene.image.ImageView;
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

    private final ApiClient api = new ApiClient(resolveBackendUrl());

    private static String resolveBackendUrl() {
        String envVal = System.getenv("GEOSENSE_API_URL");
        if (envVal != null && !envVal.isBlank()) {
            return envVal.trim();
        }
        String[] candidates = {".env", "desktopapp/.env", "../backend/.env"};
        for (String path : candidates) {
            java.io.File f = new java.io.File(path);
            if (f.isFile()) {
                try (java.util.Scanner sc = new java.util.Scanner(f, java.nio.charset.StandardCharsets.UTF_8)) {
                    while (sc.hasNextLine()) {
                        String line = sc.nextLine().trim();
                        if (line.isEmpty() || line.startsWith("#")) continue;
                        if (line.startsWith("GEOSENSE_API_URL=")) {
                            String val = line.substring("GEOSENSE_API_URL=".length()).trim();
                            if (!val.isEmpty()) return val;
                        }
                    }
                } catch (Exception ignored) {
                }
            }
        }
        return "http://localhost:8000";
    }

    private Stage primaryStage;
    private Scene loginScene;
    private Scene dashboardScene;

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
    private List<String> lastHotspots = new ArrayList<>();
    private final Map<String, Image> osmTileCache = new java.util.concurrent.ConcurrentHashMap<>();
    private final Set<String> osmLoadingTiles = java.util.concurrent.ConcurrentHashMap.newKeySet();
    private final java.net.http.HttpClient tileHttp = java.net.http.HttpClient.newBuilder()
            .connectTimeout(java.time.Duration.ofSeconds(8))
            .build();

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
        this.primaryStage = stage;
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

        dashboardScene = new Scene(root, 1360, 820);
        loginScene = buildLoginScene(stage);

        // Always show Login screen first before entering the Command Center
        stage.setScene(loginScene);
        stage.setMinWidth(1024);
        stage.setMinHeight(700);
        stage.show();
    }

    private Scene buildLoginScene(Stage stage) {
        StackPane rootStack = new StackPane();
        rootStack.setStyle("-fx-background-color: " + EMERALD_DARK + "; -fx-font-family: 'Segoe UI', system-ui, sans-serif;");

        // Background mountain hero image (matching mobile app)
        try {
            Image bgImg = null;
            var resStream = GeoSenseAuthorityApp.class.getResourceAsStream("/images/officer_hero_bg.jpg");
            if (resStream != null) {
                bgImg = new Image(resStream);
            } else {
                java.io.File fallbackFile = new java.io.File("src/main/resources/images/officer_hero_bg.jpg");
                if (fallbackFile.exists()) {
                    bgImg = new Image(fallbackFile.toURI().toString());
                }
            }
            if (bgImg != null && !bgImg.isError()) {
                ImageView bgView = new ImageView(bgImg);
                bgView.setPreserveRatio(false);
                bgView.fitWidthProperty().bind(rootStack.widthProperty());
                bgView.fitHeightProperty().bind(rootStack.heightProperty());
                rootStack.getChildren().add(bgView);
            }
        } catch (Exception ignored) {
            // Fallback to solid emerald background
        }

        // Dark Emerald / Forest gradient overlay
        Region overlay = new Region();
        overlay.setStyle("-fx-background-color: linear-gradient(to bottom, rgba(4, 34, 24, 0.78), rgba(6, 78, 59, 0.70));");
        rootStack.getChildren().add(overlay);

        VBox wrapper = new VBox(16);
        wrapper.setAlignment(Pos.CENTER);
        wrapper.setPadding(new Insets(32));

        VBox card = new VBox(14);
        card.setMaxWidth(440);
        card.setPrefWidth(440);
        card.setPadding(new Insets(28, 30, 28, 30));
        card.setStyle("-fx-background-color: #FFFFFF; -fx-background-radius: 16; -fx-effect: dropshadow(gaussian, rgba(0,0,0,0.28), 24, 0, 0, 8);");

        Label badge = new Label("SDMA AUTHORITY COMMAND CENTER");
        badge.setStyle("-fx-background-color: #DCFCE7; -fx-text-fill: #065F46; -fx-font-size: 10px; -fx-font-weight: bold; -fx-padding: 4 10; -fx-background-radius: 12;");

        Label title = new Label("GeoSense Authority Sign In");
        title.setStyle("-fx-font-size: 22px; -fx-font-weight: bold; -fx-text-fill: #0F172A;");

        Label subtitle = new Label("Sign in with an authorized Disaster Management Authority account to access live telemetry, incidents, and alert publishing.");
        subtitle.setWrapText(true);
        subtitle.setStyle("-fx-font-size: 12px; -fx-text-fill: #64748B;");

        TextField emailField = new TextField("authority@geosense.in");
        emailField.setPromptText("authority@geosense.in");
        emailField.setStyle("-fx-padding: 10 12; -fx-background-radius: 8; -fx-border-color: #CBD5E1; -fx-border-radius: 8;");

        PasswordField passField = new PasswordField();
        passField.setText("password123");
        passField.setPromptText("Password");
        passField.setStyle("-fx-padding: 10 12; -fx-background-radius: 8; -fx-border-color: #CBD5E1; -fx-border-radius: 8;");

        Label errorLabel = new Label();
        errorLabel.setWrapText(true);
        errorLabel.setVisible(false);
        errorLabel.setManaged(false);
        errorLabel.setStyle("-fx-background-color: #FEE2E2; -fx-text-fill: #B91C1C; -fx-font-size: 12px; -fx-font-weight: bold; -fx-padding: 10 12; -fx-background-radius: 8;");

        Button signInBtn = new Button("Sign In to Command Center");
        signInBtn.setMaxWidth(Double.MAX_VALUE);
        signInBtn.setStyle(BTN_PRIMARY + " -fx-padding: 12 16; -fx-font-size: 14px;");

        Runnable doLogin = () -> {
            String email = emailField.getText().trim();
            String pass = passField.getText();
            if (email.isEmpty() || pass.isEmpty()) {
                errorLabel.setText("Please enter your email/ID and password.");
                errorLabel.setVisible(true);
                errorLabel.setManaged(true);
                return;
            }
            errorLabel.setVisible(false);
            errorLabel.setManaged(false);
            signInBtn.setDisable(true);
            signInBtn.setText("Signing in...");

            new Thread(() -> {
                try {
                    String resp = api.login(email, pass);
                    String role = ApiClient.extractJsonString(resp, "role");
                    String fullName = ApiClient.extractJsonString(resp, "full_name");
                    if (!"AUTHORITY".equalsIgnoreCase(role) && !"ADMIN".equalsIgnoreCase(role)) {
                        api.clearToken();
                        throw new RuntimeException("Access denied: role '" + role + "' cannot access Authority Command Center.");
                    }
                    String ch = api.getChannelStatus();
                    Platform.runLater(() -> {
                        String displayName = fullName.isEmpty() ? email : fullName;
                        userNameLabel.setText(displayName);
                        userRoleLabel.setText(role);
                        String[] parts = displayName.trim().split("\\s+");
                        String initials = parts.length >= 2
                                ? ("" + parts[0].charAt(0) + parts[1].charAt(0)).toUpperCase()
                                : displayName.substring(0, Math.min(2, displayName.length())).toUpperCase();
                        userAvatarLabel.setText(initials);
                        channelStatusLabel.setText("Channels: " + ch);
                        signInBtn.setDisable(false);
                        signInBtn.setText("Sign In to Command Center");
                        stage.setScene(dashboardScene);
                    });
                    refreshAllData();
                } catch (Exception ex) {
                    Platform.runLater(() -> {
                        errorLabel.setText("Login failed: " + ex.getMessage());
                        errorLabel.setVisible(true);
                        errorLabel.setManaged(true);
                        signInBtn.setDisable(false);
                        signInBtn.setText("Sign In to Command Center");
                    });
                }
            }).start();
        };

        signInBtn.setOnAction(e -> doLogin.run());
        passField.setOnAction(e -> doLogin.run());

        Label footerNote = new Label("Meghalaya State Disaster Management Authority • GeoSense");
        footerNote.setStyle("-fx-font-size: 11px; -fx-text-fill: #94A3B8; -fx-padding: 6 0 0 0;");

        card.getChildren().addAll(
                badge, title, subtitle,
                new Label("Authority Email or ID") {{ setStyle("-fx-font-size:12px; -fx-font-weight:bold; -fx-text-fill:#334155;"); }}, emailField,
                new Label("Password") {{ setStyle("-fx-font-size:12px; -fx-font-weight:bold; -fx-text-fill:#334155;"); }}, passField,
                errorLabel,
                signInBtn,
                footerNote
        );

        wrapper.getChildren().add(card);
        rootStack.getChildren().add(wrapper);
        return new Scene(rootStack, 1360, 820);
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
        clock.setMinWidth(Region.USE_PREF_SIZE);
        Label livePill = new Label("● LIVE");
        livePill.setStyle("-fx-background-color: #10B981; -fx-text-fill: #FFFFFF; -fx-font-size: 10px; -fx-font-weight: bold; -fx-padding: 4 10; -fx-background-radius: 12;");
        livePill.setMinWidth(Region.USE_PREF_SIZE);

        Button refreshBtn = new Button("Refresh");
        refreshBtn.setStyle("-fx-background-color: #FFFFFF; -fx-text-fill: #053324; -fx-font-weight: bold; -fx-background-radius: 8; -fx-padding: 6 12; cursor: hand;");
        refreshBtn.setMinWidth(Region.USE_PREF_SIZE);
        refreshBtn.setOnAction(e -> runAsync(this::refreshAllData));

        Button signOutBtn = new Button("Sign Out");
        signOutBtn.setStyle("-fx-background-color: rgba(255,255,255,0.16); -fx-text-fill: #FFFFFF; -fx-font-weight: bold; -fx-background-radius: 8; -fx-padding: 6 12; cursor: hand;");
        signOutBtn.setMinWidth(Region.USE_PREF_SIZE);
        signOutBtn.setOnAction(e -> {
            api.clearToken();
            stage.setScene(loginScene);
        });

        userAvatarLabel = new Label("SD");
        userAvatarLabel.setStyle("-fx-background-color: #0D8A5E; -fx-text-fill: #FFFFFF; -fx-font-weight: bold; -fx-font-size: 12px; -fx-background-radius: 18;");
        userAvatarLabel.setPrefSize(34, 34);
        userAvatarLabel.setMinSize(34, 34);
        userAvatarLabel.setMaxSize(34, 34);
        userAvatarLabel.setAlignment(Pos.CENTER);

        userNameLabel = new Label("SDMA Director");
        userNameLabel.setStyle("-fx-text-fill: #FFFFFF; -fx-font-weight: bold; -fx-font-size: 12px;");
        userNameLabel.setMinWidth(Region.USE_PREF_SIZE);
        userRoleLabel = new Label("AUTHORITY");
        userRoleLabel.setStyle("-fx-text-fill: #A7F3D0; -fx-font-size: 10px;");
        userRoleLabel.setMinWidth(Region.USE_PREF_SIZE);
        VBox userInfo = new VBox(1, userNameLabel, userRoleLabel);
        userInfo.setAlignment(Pos.CENTER_LEFT);
        userInfo.setMinWidth(Region.USE_PREF_SIZE);
        userInfo.setMaxHeight(Region.USE_PREF_SIZE);

        HBox right = new HBox(10, clock, livePill, refreshBtn, signOutBtn, userAvatarLabel, userInfo);
        right.setAlignment(Pos.CENTER_RIGHT);
        right.setMinWidth(Region.USE_PREF_SIZE);
        right.setMaxHeight(Region.USE_PREF_SIZE);

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
        runBtn.setMaxWidth(Double.MAX_VALUE);
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
        riskTrendChart.setAnimated(false);
        VBox trendCard = new VBox(8, new Label("Risk trend (Cherrapunji)") {{ setStyle("-fx-font-weight:bold; -fx-font-size:14px;"); }}, riskTrendChart);
        trendCard.setStyle(CARD_STYLE);
        HBox.setHgrow(trendCard, Priority.ALWAYS);

        VBox recentCard = new VBox(8, new Label("Recent incidents") {{ setStyle("-fx-font-weight:bold; -fx-font-size:14px;"); }}, recentIncidentsBox);
        recentCard.setStyle(CARD_STYLE);
        recentCard.setPrefWidth(320);
        recentCard.setMinWidth(280);

        Button qaWarn = new Button("Issue warning"); qaWarn.setStyle(BTN_SECONDARY);
        qaWarn.setMaxWidth(Double.MAX_VALUE); qaWarn.setMinWidth(Region.USE_PREF_SIZE);
        qaWarn.setOnAction(e -> switchPage("Alerts & Communication", "Review risk alerts, approve public advisories & track Email + FCM delivery"));

        Button qaOps = new Button("Deploy officer"); qaOps.setStyle(BTN_SECONDARY);
        qaOps.setMaxWidth(Double.MAX_VALUE); qaOps.setMinWidth(Region.USE_PREF_SIZE);
        qaOps.setOnAction(e -> switchPage("Field Operations", "Coordinate field officers, deploy response teams & monitor inspections"));

        Button qaRes = new Button("Allocate relief"); qaRes.setStyle(BTN_SECONDARY);
        qaRes.setMaxWidth(Double.MAX_VALUE); qaRes.setMinWidth(Region.USE_PREF_SIZE);
        qaRes.setOnAction(e -> switchPage("Resources & Shelter", "Maintain shelter readiness, verify medical assets & coordinate relief"));

        Button qaRep = new Button("Generate report"); qaRep.setStyle(BTN_PRIMARY);
        qaRep.setMaxWidth(Double.MAX_VALUE); qaRep.setMinWidth(Region.USE_PREF_SIZE);
        qaRep.setOnAction(e -> switchPage("Reports & Analytics", "Evaluate district exposure, response outcomes & generate situation reports"));

        GridPane qaGrid = new GridPane();
        qaGrid.setHgap(10); qaGrid.setVgap(10);
        ColumnConstraints col1 = new ColumnConstraints(); col1.setPercentWidth(50);
        ColumnConstraints col2 = new ColumnConstraints(); col2.setPercentWidth(50);
        qaGrid.getColumnConstraints().addAll(col1, col2);
        qaGrid.add(qaWarn, 0, 0); qaGrid.add(qaOps, 1, 0);
        qaGrid.add(qaRes, 0, 1); qaGrid.add(qaRep, 1, 1);

        VBox qaCard = new VBox(10, new Label("Quick actions") {{ setStyle("-fx-font-weight:bold; -fx-font-size:14px;"); }}, qaGrid);
        qaCard.setStyle(CARD_STYLE);
        qaCard.setPrefWidth(330);
        qaCard.setMinWidth(310);

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

        String trendsJson = "";
        try {
            trendsJson = api.getRiskTrends("loc_25.270_91.732");
        } catch (Exception ignored) {}

        String latestHotspotRisk = "";
        try {
            latestHotspotRisk = api.request("GET", "/risk/loc_25.285_91.721", null);
        } catch (Exception ignored) {}

        List<String> incObjs = ApiClient.splitJsonObjectsInArray(incsJson, "incidents");
        List<String> resObjs = ApiClient.splitJsonObjectsInArray(resJson, "resources");
        List<String> alertObjs = ApiClient.splitJsonObjectsInArray(alertsJson, "alerts");
        List<String> inspObjs = ApiClient.splitJsonObjectsInArray(inspJson, "inspections");
        List<String> hsObjs = ApiClient.splitJsonObjectsInArray(hsJson, "hotspots");
        List<String> trendPts = trendsJson.isEmpty() ? List.of() : ApiClient.splitJsonObjectsInArray(trendsJson, "timeline");

        // Sum state distribution counts from /authority/analytics
        int modCount = 0;
        int lowCount = 0;
        var modMatcher = java.util.regex.Pattern.compile("\"MODERATE\"\\s*:\\s*(\\d+)").matcher(analytics);
        while (modMatcher.find()) modCount += Integer.parseInt(modMatcher.group(1));
        var lowMatcher = java.util.regex.Pattern.compile("\"LOW\"\\s*:\\s*(\\d+)").matcher(analytics);
        while (lowMatcher.find()) lowCount += Integer.parseInt(lowMatcher.group(1));
        final int finalModCount = modCount;
        final int finalLowCount = lowCount;
        final String finalLatestRisk = latestHotspotRisk;

        Platform.runLater(() -> {
            int high = Integer.parseInt(ApiClient.extractJsonNumber(dash, "high_risk_locations"));
            int crit = Integer.parseInt(ApiClient.extractJsonNumber(dash, "critical_risk_locations"));
            int totalRisk = Integer.parseInt(ApiClient.extractJsonNumber(dash, "total_risk_assessments"));
            int pendingInc = Integer.parseInt(ApiClient.extractJsonNumber(dash, "pending"));
            kpiHighRisk.setText(String.valueOf(high + crit));
            kpiModRisk.setText(String.valueOf(finalModCount));
            kpiLowRisk.setText(String.valueOf(finalLowCount));
            kpiActiveInc.setText(ApiClient.extractJsonNumber(dash, "total"));
            kpiShelters.setText(ApiClient.extractJsonNumber(dash, "verified_resources"));
            incidentBadge.setText(String.valueOf(pendingInc));
            syncLabel.setText("Last sync: " + LocalDateTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss")));

            if (!finalLatestRisk.isEmpty()) {
                double score = Double.parseDouble(ApiClient.extractJsonNumber(finalLatestRisk, "risk_score"));
                String locName = ApiClient.extractJsonString(finalLatestRisk, "location_name");
                String explain = ApiClient.extractJsonString(finalLatestRisk, "explanation");
                String r24 = ApiClient.extractJsonNumber(finalLatestRisk, "rainfall_24h_mm");
                String slope = ApiClient.extractJsonNumber(finalLatestRisk, "slope_deg");
                gaugeScoreLabel.setText(String.format("%.0f", score));
                gaugeArc.setLength(-(score / 100.0) * 360.0);
                rain24Label.setText(("0".equals(r24) ? "--" : r24) + " mm");
                slopeLabel.setText(("0".equals(slope) ? "--" : slope + "°") + (locName.isEmpty() ? "" : " (" + locName + ")"));
                if (!explain.isEmpty()) xaiWhyLabel.setText(explain);
            }

            riskTrendChart.getData().clear();
            if (!trendPts.isEmpty()) {
                XYChart.Series<String, Number> ts = new XYChart.Series<>();
                int startIdx = Math.max(0, trendPts.size() - 6);
                for (int i = startIdx; i < trendPts.size(); i++) {
                    double sc = Double.parseDouble(ApiClient.extractJsonNumber(trendPts.get(i), "risk_score"));
                    String tStr = ApiClient.extractJsonString(trendPts.get(i), "assessment_time");
                    String lbl = tStr.length() >= 16 ? tStr.substring(5, 10) + " " + tStr.substring(11, 16) : "T" + (i + 1);
                    ts.getData().add(new XYChart.Data<>(lbl, sc));
                }
                riskTrendChart.getData().add(ts);
            }

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

            lastHotspots = hsObjs;
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

    private static double lonToTileX(double lon, int zoom) {
        return (lon + 180.0) / 360.0 * (1 << zoom);
    }

    private static double latToTileY(double lat, int zoom) {
        double rad = Math.toRadians(lat);
        return (1.0 - Math.log(Math.tan(rad) + 1.0 / Math.cos(rad)) / Math.PI) / 2.0 * (1 << zoom);
    }

    private void fetchOsmTileAsync(int z, int x, int y) {
        String key = z + "/" + x + "/" + y;
        if (osmTileCache.containsKey(key) || !osmLoadingTiles.add(key)) return;
        String url = "https://tile.openstreetmap.org/" + z + "/" + x + "/" + y + ".png";
        new Thread(() -> {
            try {
                var req = java.net.http.HttpRequest.newBuilder()
                        .uri(java.net.URI.create(url))
                        .header("User-Agent", "GeoSense-Authority-Desktop/1.0")
                        .timeout(java.time.Duration.ofSeconds(10))
                        .GET()
                        .build();
                var resp = tileHttp.send(req, java.net.http.HttpResponse.BodyHandlers.ofInputStream());
                if (resp.statusCode() == 200) {
                    Image tile = new Image(resp.body());
                    if (!tile.isError()) {
                        osmTileCache.put(key, tile);
                        Platform.runLater(() -> {
                            drawMapCanvas(dashMapCanvas, lastHotspots);
                            drawMapCanvas(monitorMapCanvas, lastHotspots);
                        });
                    }
                }
            } catch (Exception ignored) {
            } finally {
                osmLoadingTiles.remove(key);
            }
        }).start();
    }

    private void drawMapCanvas(Canvas canvas, List<String> hotspots) {
        GraphicsContext gc = canvas.getGraphicsContext2D();
        double w = canvas.getWidth(), h = canvas.getHeight();
        gc.setFill(Color.web("#E2EAE5"));
        gc.fillRoundRect(0, 0, w, h, 10, 10);

        // Web Mercator OpenStreetMap centered on Meghalaya / East Khasi Hills
        int zoom = 9;
        double centerLat = 25.43;
        double centerLon = 91.75;
        double centerX = lonToTileX(centerLon, zoom);
        double centerY = latToTileY(centerLat, zoom);

        double topLeftTileX = centerX - (w / 2.0) / 256.0;
        double topLeftTileY = centerY - (h / 2.0) / 256.0;
        int minTx = (int) Math.floor(topLeftTileX);
        int maxTx = (int) Math.floor(centerX + (w / 2.0) / 256.0);
        int minTy = (int) Math.floor(topLeftTileY);
        int maxTy = (int) Math.floor(centerY + (h / 2.0) / 256.0);
        int maxIdx = (1 << zoom) - 1;

        boolean anyTile = false;
        for (int tx = minTx; tx <= maxTx; tx++) {
            for (int ty = minTy; ty <= maxTy; ty++) {
                if (tx < 0 || tx > maxIdx || ty < 0 || ty > maxIdx) continue;
                String key = zoom + "/" + tx + "/" + ty;
                Image tile = osmTileCache.get(key);
                double drawX = w / 2.0 + (tx - centerX) * 256.0;
                double drawY = h / 2.0 + (ty - centerY) * 256.0;
                if (tile != null) {
                    gc.drawImage(tile, drawX, drawY, 256, 256);
                    anyTile = true;
                } else {
                    fetchOsmTileAsync(zoom, tx, ty);
                }
            }
        }

        if (!anyTile) {
            gc.setStroke(Color.web("#CBD5E1"));
            gc.setLineWidth(1);
            for (int x = 40; x < w; x += 60) gc.strokeLine(x, 0, x, h);
            for (int y = 40; y < h; y += 60) gc.strokeLine(0, y, w, y);
        }

        // Plot unique hotspots at exact OpenStreetMap Web Mercator coordinates
        List<double[]> placedLabels = new ArrayList<>();
        Set<String> seenNames = new HashSet<>();

        for (int i = 0; i < hotspots.size(); i++) {
            String hObj = hotspots.get(i);
            String name = ApiClient.extractJsonString(hObj, "location_name");
            if (name.isEmpty() || !seenNames.add(name)) continue;
            String cat = ApiClient.extractJsonString(hObj, "risk_category");
            var coordM = java.util.regex.Pattern.compile("\"coordinates\"\\s*:\\s*\\[\\s*(-?\\d+(?:\\.\\d+)?)\\s*,\\s*(-?\\d+(?:\\.\\d+)?)\\s*\\]").matcher(hObj);
            if (!coordM.find()) continue;

            double lon = Double.parseDouble(coordM.group(1));
            double lat = Double.parseDouble(coordM.group(2));
            double px = w / 2.0 + (lonToTileX(lon, zoom) - centerX) * 256.0;
            double py = h / 2.0 + (latToTileY(lat, zoom) - centerY) * 256.0;
            if (px < 10 || px > w - 10 || py < 10 || py > h - 10) continue;

            gc.setFill(Color.web("#FFFFFF"));
            gc.fillOval(px - 7, py - 7, 14, 14);
            gc.setFill("HIGH".equalsIgnoreCase(cat) ? Color.web("#EA580C") : Color.web("#DC2626"));
            gc.fillOval(px - 5, py - 5, 10, 10);

            double lx = px + 9;
            double ly = py + 4;
            for (int attempt = 0; attempt < 8; attempt++) {
                boolean collides = false;
                for (double[] box : placedLabels) {
                    if (Math.abs(lx - box[0]) < 120 && Math.abs(ly - box[1]) < 18) {
                        collides = true;
                        break;
                    }
                }
                if (!collides) break;
                ly = (attempt % 2 == 0) ? py + 18 + (attempt / 2) * 18 : py - 14 - (attempt / 2) * 18;
            }
            lx = Math.max(8, Math.min(w - 148, lx));
            ly = Math.max(16, Math.min(h - 10, ly));
            placedLabels.add(new double[]{lx, ly});

            gc.setFill(Color.web("#FFFFFF", 0.90));
            gc.fillRoundRect(lx - 3, ly - 11, Math.min(145, name.length() * 6.5 + 8), 15, 4, 4);
            gc.setFill(Color.web("#0F172A"));
            gc.fillText(name, lx, ly);
        }

        // OSM Attribution badge
        gc.setFill(Color.web("#FFFFFF", 0.85));
        gc.fillRoundRect(w - 132, h - 18, 128, 15, 4, 4);
        gc.setFill(Color.web("#475569"));
        gc.fillText("© OpenStreetMap", w - 126, h - 7);
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
