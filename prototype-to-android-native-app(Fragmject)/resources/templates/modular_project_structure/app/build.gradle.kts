plugins {
    id("android.application")
    id("hilt")
}

android {
    namespace = "{{package_name}}.app"

    defaultConfig {
        applicationId = "{{package_name}}"
        versionCode = 1
        versionName = "1.0.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
}

dependencies {
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.kotlinx.coroutines.android)

    implementation(project(":core:common"))
    implementation(project(":core:component-runtime"))
    implementation(project(":core:designsystem"))
    implementation(project(":core:monitor"))
    implementation(project(":core:router"))
    implementation(project(":core:startup"))
    {{feature_impl_dependencies}}

    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.compose.ui.test.junit4)
    debugImplementation(libs.androidx.compose.ui.tooling)
}
