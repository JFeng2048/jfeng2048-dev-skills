import com.android.build.api.dsl.LibraryExtension
import org.gradle.api.artifacts.VersionCatalogsExtension
import org.gradle.kotlin.dsl.configure
import org.jetbrains.kotlin.gradle.dsl.KotlinAndroidProjectExtension

plugins {
    id("com.android.library")
    id("org.jetbrains.kotlin.android")
}

val catalog = extensions.getByType<VersionCatalogsExtension>().named("libs")
val jdkVersion = catalog.findVersion("jdk").get().requiredVersion

extensions.configure<LibraryExtension> {
    compileSdk = catalog.findVersion("compileSdk").get().requiredVersion.toInt()
    defaultConfig {
        minSdk = catalog.findVersion("minSdk").get().requiredVersion.toInt()
    }
    compileOptions {
        sourceCompatibility = JavaVersion.toVersion(jdkVersion)
        targetCompatibility = JavaVersion.toVersion(jdkVersion)
    }
}

extensions.configure<KotlinAndroidProjectExtension> {
    jvmToolchain(jdkVersion.toInt())
}
