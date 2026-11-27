$m2 = "$env:USERPROFILE\.m2\repository\org\openjfx"
$cp = @(
    "$m2\javafx-base\21\javafx-base-21-win.jar",
    "$m2\javafx-graphics\21\javafx-graphics-21-win.jar",
    "$m2\javafx-controls\21\javafx-controls-21-win.jar"
) -join ";"

New-Item -ItemType Directory -Force -Path "out" | Out-Null
javac --module-path $cp --add-modules javafx.controls,javafx.graphics -d out src/main/java/com/geosense/authority/*.java
if ($LASTEXITCODE -eq 0) {
    java --module-path $cp --add-modules javafx.controls,javafx.graphics -cp out com.geosense.authority.GeoSenseAuthorityApp
}
