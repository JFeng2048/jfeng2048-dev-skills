import org.gradle.api.artifacts.VersionCatalogsExtension

plugins {
    id("com.google.dagger.hilt.android")
    id("com.google.devtools.ksp")
}

val catalog = extensions.getByType<VersionCatalogsExtension>().named("libs")

dependencies {
    add("implementation", catalog.findLibrary("hilt-android").get())
    add("ksp", catalog.findLibrary("hilt-compiler").get())
}
