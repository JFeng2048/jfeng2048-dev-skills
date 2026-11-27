plugins {
    id("android.compose-library")
}

android {
    namespace = "{{package_name}}.core.designsystem"
}

dependencies {
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.material3)
}
