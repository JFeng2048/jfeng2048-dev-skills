import org.jetbrains.kotlin.gradle.dsl.KotlinJvmProjectExtension
import org.gradle.api.artifacts.VersionCatalogsExtension
import org.gradle.kotlin.dsl.configure

plugins {
    id("org.jetbrains.kotlin.jvm")
}

val catalog = extensions.getByType<VersionCatalogsExtension>().named("libs")

extensions.configure<KotlinJvmProjectExtension> {
    jvmToolchain(catalog.findVersion("jdk").get().requiredVersion.toInt())
}
