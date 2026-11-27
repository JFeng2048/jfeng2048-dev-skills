plugins {
    id("android.library")
}

android {
    namespace = "{{package_name}}.core.router"
}

dependencies {
    api(libs.androidx.navigation.compose)
}
