pluginManagement {
    includeBuild("build-logic")
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "{{project_name}}"
include(
    ":app",
    ":core:common",
    ":core:component-runtime",
    ":core:designsystem",
    ":core:ipc",
    ":core:monitor",
    ":core:network",
    ":core:router",
    ":core:startup",
    ":core:storage",
)
{{feature_module_includes}}
