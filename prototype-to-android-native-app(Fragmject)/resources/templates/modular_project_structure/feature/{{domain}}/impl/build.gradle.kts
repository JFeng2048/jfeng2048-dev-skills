plugins {
    id("android.compose-library")
    id("hilt")
}

android {
    namespace = "{{package_name}}.feature.{{domain}}.impl"
}

dependencies {
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.navigation.compose)

    implementation(project(":feature:{{domain}}:api"))
    implementation(project(":core:common"))
    implementation(project(":core:designsystem"))
    implementation(project(":core:network"))
    implementation(project(":core:storage"))
    implementation(project(":core:monitor"))
    testImplementation(libs.junit)
}
