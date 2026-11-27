plugins {
    id("android.library")
}

android {
    namespace = "{{package_name}}.core.network"
}

dependencies {
    implementation(libs.okhttp)
}
