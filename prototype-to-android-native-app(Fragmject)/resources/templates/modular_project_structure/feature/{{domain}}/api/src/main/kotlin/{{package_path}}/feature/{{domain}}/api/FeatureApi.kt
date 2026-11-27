package {{package_name}}.feature.{{domain}}.api

import {{package_name}}.core.router.FeatureEntry

interface {{domain_pascal}}FeatureApi : FeatureEntry

object {{domain_pascal}}Routes {
    const val START = "{{domain_route}}"
}
