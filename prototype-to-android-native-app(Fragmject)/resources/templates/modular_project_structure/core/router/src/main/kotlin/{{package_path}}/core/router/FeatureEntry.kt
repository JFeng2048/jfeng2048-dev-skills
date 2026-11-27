package {{package_name}}.core.router

import androidx.navigation.NavGraphBuilder
import androidx.navigation.NavHostController

interface FeatureEntry {
    val startDestination: String
    val isDefaultStartDestination: Boolean

    fun registerGraph(
        builder: NavGraphBuilder,
        navController: NavHostController,
    )
}
