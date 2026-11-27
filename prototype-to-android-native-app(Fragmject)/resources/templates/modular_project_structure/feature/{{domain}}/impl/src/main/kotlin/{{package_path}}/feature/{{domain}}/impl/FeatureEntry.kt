package {{package_name}}.feature.{{domain}}.impl

import androidx.navigation.NavGraphBuilder
import androidx.navigation.NavHostController
import androidx.navigation.compose.composable
import {{package_name}}.feature.{{domain}}.api.{{domain_pascal}}FeatureApi
import {{package_name}}.feature.{{domain}}.api.{{domain_pascal}}Routes
import {{package_name}}.feature.{{domain}}.impl.ui.FeatureHomeScreen
import javax.inject.Inject

class {{domain_pascal}}FeatureEntry @Inject constructor() : {{domain_pascal}}FeatureApi {
    override val startDestination: String = {{domain_pascal}}Routes.START
    override val isDefaultStartDestination: Boolean = {{feature_is_default}}

    override fun registerGraph(
        builder: NavGraphBuilder,
        navController: NavHostController,
    ) {
        builder.composable(route = startDestination) {
            FeatureHomeScreen(title = "{{feature_page_title}}")
        }
    }
}
