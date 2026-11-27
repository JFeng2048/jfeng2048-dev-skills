plugins {
    id("android.library")
}

android {
    namespace = "{{package_name}}.feature.{{domain}}.api"
}

dependencies {
    api(project(":core:router"))
}
