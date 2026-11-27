import org.gradle.api.GradleException
import org.gradle.api.artifacts.ExternalModuleDependency
import org.gradle.api.artifacts.ProjectDependency
import org.w3c.dom.Element
import javax.xml.parsers.DocumentBuilderFactory

val validateArchitecture by tasks.registering {
    group = "verification"
    description = "Checks module dependency direction and Android component export declarations."

    doLast {
        val problems = mutableListOf<String>()
        val modules = rootProject.subprojects
        val dependencyGraph = modules.associate { module ->
            module.path to module.configurations
                .flatMap { it.dependencies.withType(ProjectDependency::class.java) }
                .map { it.dependencyProject.path }
                .toSet()
        }
        val visited = mutableSetOf<String>()
        val visiting = linkedSetOf<String>()

        fun checkCycles(modulePath: String) {
            if (modulePath in visiting) {
                val cycle = (visiting.dropWhile { it != modulePath } + modulePath)
                    .joinToString(" -> ")
                problems += "Module dependency cycle: $cycle"
                return
            }
            if (!visited.add(modulePath)) return
            visiting += modulePath
            dependencyGraph[modulePath].orEmpty()
                .filter { it in dependencyGraph }
                .forEach(::checkCycles)
            visiting -= modulePath
        }

        dependencyGraph.keys.forEach(::checkCycles)

        modules.forEach { module ->
            val projectDependencies = dependencyGraph[module.path].orEmpty()

            projectDependencies.forEach { dependency ->
                if (module.path.startsWith(":core:") && dependency.startsWith(":feature:")) {
                    problems += "${module.path} must not depend on feature module $dependency"
                }
                val feature = Regex(":feature:([^:]+):(api|impl)").matchEntire(module.path)
                val target = Regex(":feature:([^:]+):(api|impl)").matchEntire(dependency)
                if (feature != null && target != null) {
                    val sourceDomain = feature.groupValues[1]
                    val sourceKind = feature.groupValues[2]
                    val targetDomain = target.groupValues[1]
                    val targetKind = target.groupValues[2]
                    if (sourceKind == "api" && targetKind == "impl") {
                        problems += "${module.path} API must not depend on implementation $dependency"
                    }
                    if (sourceKind == "impl" && targetKind == "impl" && sourceDomain != targetDomain) {
                        problems += "${module.path} must depend on $dependency's API, not implementation"
                    }
                }
                if (module.path != ":app" && dependency == ":app") {
                    problems += "${module.path} must not depend on the app composition root"
                }
            }

            val feature = Regex(":feature:([^:]+):impl").matchEntire(module.path)
            if (feature != null) {
                val apiPath = ":feature:${feature.groupValues[1]}:api"
                if (apiPath !in projectDependencies) {
                    problems += "${module.path} must depend on its own API module $apiPath"
                }
                if (apiPath !in modules.map { it.path }) {
                    problems += "Missing feature API module $apiPath"
                }
            }

            module.configurations.forEach { configuration ->
                configuration.dependencies
                    .withType(ExternalModuleDependency::class.java)
                    .forEach { dependency ->
                        val version = dependency.version.orEmpty().lowercase()
                        if ("+" in version || version == "latest.release") {
                            problems += "${module.path}:${configuration.name} uses a dynamic dependency version"
                        }
                    }
            }
        }

        modules.mapNotNull { module ->
            Regex(":feature:([^:]+):api").matchEntire(module.path)?.groupValues?.get(1)
        }.forEach { domain ->
            val implementationPath = ":feature:$domain:impl"
            val appDependencies = rootProject.project(":app").configurations
                .flatMap { it.dependencies.withType(ProjectDependency::class.java) }
                .map { it.dependencyProject.path }
                .toSet()
            if (implementationPath !in appDependencies) {
                problems += ":app must assemble $implementationPath"
            }
        }

        val androidNamespace = "http://schemas.android.com/apk/res/android"
        val componentTags = setOf("activity", "activity-alias", "service", "receiver", "provider")
        val manifests = rootProject.fileTree(rootDir) {
            include("**/src/main/AndroidManifest.xml")
            exclude("**/build/**", "**/.gradle/**")
        }
        manifests.files.forEach { manifest ->
            try {
                val factory = DocumentBuilderFactory.newInstance().apply {
                    isNamespaceAware = true
                    setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)
                    setFeature("http://xml.org/sax/features/external-general-entities", false)
                    setFeature("http://xml.org/sax/features/external-parameter-entities", false)
                }
                val document = factory.newDocumentBuilder().parse(manifest)
                val nodes = document.getElementsByTagName("*")
                for (index in 0 until nodes.length) {
                    val element = nodes.item(index) as? Element ?: continue
                    val tag = element.localName ?: element.tagName.substringAfter(":")
                    if (tag in componentTags) {
                        val componentName = element.getAttributeNS(androidNamespace, "name")
                        val exported = element.getAttributeNS(androidNamespace, "exported")
                        if (componentName.isBlank() || exported !in setOf("true", "false")) {
                            problems += "${manifest.relativeTo(rootDir)} has a component without explicit android:name/android:exported"
                        }
                    }
                }
            } catch (error: Exception) {
                problems += "Cannot parse ${manifest.relativeTo(rootDir)}: ${error.message}"
            }
        }

        if (problems.isNotEmpty()) {
            throw GradleException(
                "Architecture validation failed:\n" + problems.distinct().joinToString("\n") { " - $it" },
            )
        }
        logger.lifecycle("Architecture validation passed for ${modules.size} modules.")
    }
}
