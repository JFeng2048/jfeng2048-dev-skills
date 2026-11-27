plugins {
    id("android.library")
    id("ksp")
}

android {
    namespace = "{{package_name}}.core.storage"
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.room.runtime)
    implementation(libs.androidx.room.ktx)
    ksp(libs.androidx.room.compiler)
    implementation(libs.androidx.datastore.preferences)
}
