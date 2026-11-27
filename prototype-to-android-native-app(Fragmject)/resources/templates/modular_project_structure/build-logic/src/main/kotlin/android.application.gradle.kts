import com.android.build.api.dsl.ApplicationExtension
import org.gradle.api.artifacts.VersionCatalogsExtension
import org.gradle.kotlin.dsl.configure
import org.jetbrains.kotlin.gradle.dsl.KotlinAndroidProjectExtension

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

val catalog = extensions.getByType<VersionCatalogsExtension>().named("libs")
val jdkVersion = catalog.findVersion("jdk").get().requiredVersion

extensions.configure<ApplicationExtension> {
    compileSdk = catalog.findVersion("compileSdk").get().requiredVersion.toInt()
    defaultConfig {
        minSdk = catalog.findVersion("minSdk").get().requiredVersion.toInt()
        targetSdk = catalog.findVersion("targetSdk").get().requiredVersion.toInt()
    }
    compileOptions {
        sourceCompatibility = JavaVersion.toVersion(jdkVersion)
        targetCompatibility = JavaVersion.toVersion(jdkVersion)
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
}

extensions.configure<KotlinAndroidProjectExtension> {
    jvmToolchain(jdkVersion.toInt())
}
